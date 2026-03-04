import asyncio
import json
import os
import re
from datetime import datetime
from playwright.async_api import async_playwright
# 如果运行报错，请确保安装了 python-telegram-bot
from telegram import Update
from telegram.ext import ApplicationBuilder, CommandHandler, ContextTypes, Defaults

# ================= 配置部分 (建议发布到 GitHub 前删除具体数值) =================
# 建议：通过环境变量获取，或提醒用户在此处填写
TG_TOKEN = os.getenv("TG_TOKEN", "在此处填写你的机器人Token") 
REFRESH_INTERVAL = 60  # 监控轮询间隔（秒）

# 数据库文件路径（本地存储，无需更改）
USER_DB_FILE = "renaiss_users_data.json"
DEAL_DB_FILE = "renaiss_v12_deals.json"
ACTIVITY_DB_FILE = "renaiss_user_activity.json"

# 基础跳转链接
DETAIL_URL_PREFIX = "https://www.renaiss.xyz/card/"

# 终端显示颜色配置
GREEN = "\033[32m"
YELLOW = "\033[33m"
BLUE = "\033[34m"
CYAN = "\033[36m"
RED = "\033[31m"
RESET = "\033[0m"
# ===========================================================================

def load_json(f):
    """加载本地 JSON 数据库"""
    if not os.path.exists(f): return {}
    try:
        with open(f, 'r', encoding='utf-8') as file:
            data = json.load(file)
            return data if isinstance(data, dict) else {}
    except: return {}

def save_json(f, data):
    """保存数据到本地 JSON 文件"""
    try:
        with open(f, 'w', encoding='utf-8') as file: 
            json.dump(data, file, indent=4, ensure_ascii=False)
    except: pass

# --- 核心引擎：市场扫描 ---
async def scan_marketplace_v33_original(page):
    """
    使用 v33 原生引擎逻辑扫描市场。
    功能：寻找标价远低于 FMV (市场参考价) 的卡牌。
    """
    try:
        print(f"[{datetime.now().strftime('%H:%M:%S')}] {BLUE}🔍 市场扫描中...{RESET}")
        await page.goto("https://www.renaiss.xyz/marketplace", wait_until="networkidle", timeout=60000)
        
        # 模拟滚动以加载更多内容
        for _ in range(3):
            await page.mouse.wheel(0, 1000)
            await asyncio.sleep(2)
            
        return await page.evaluate(r"""
            () => {
                const seen = new Set(); const cards = [];
                // 筛选包含 FMV 信息的 div 容器
                const fmvDivs = Array.from(document.querySelectorAll('div')).filter(d => d.innerText && d.innerText.includes('FMV') && d.innerText.length < 500);
                
                fmvDivs.forEach(div => {
                    // 正则匹配：卡牌名称、价格、FMV
                    const match = div.innerText.match(/([^\n\$]+)\n\$\s?([\d,.]+)\nFMV\n\$\s?([\d,.]+)/);
                    if (match) {
                        const title = match[1].trim(), price = match[2].replace(',', '');
                        if (seen.has(`${title}_${price}`)) return;
                        seen.add(`${title}_${price}`);
                        
                        let foundId = null, current = div;
                        // 向上寻找父元素获取卡牌长 ID
                        for (let i = 0; i < 15; i++) {
                            if (!current) break;
                            for (let attr of current.attributes) { 
                                if (/\d{70,80}/.test(attr.value)) { foundId = attr.value.match(/\d{70,80}/)[0]; break; } 
                            }
                            if (foundId) break;
                            const link = current.querySelector('a[href*="/card/"]');
                            if (link && /\d{70,80}/.test(link.href)) { foundId = link.href.match(/\d{70,80}/)[0]; break; }
                            current = current.parentElement;
                        }
                        cards.push({ title, price, fmv: match[3].replace(',', ''), id: foundId });
                    }
                });
                return cards;
            }
        """)
    except Exception as e:
        print(f"{RED}❌ 扫描异常: {e}{RESET}")
        return []

async def monitor_loop(application):
    """主监控循环：处理市场捡漏推送和用户动态追踪"""
    print(f"[{datetime.now().strftime('%H:%M:%S')}] {GREEN}🤖 监控系统启动 | 防重复推送已开启{RESET}")
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True) # 改为 False 可看到浏览器操作
        context = await browser.new_context(user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36...")
        
        while True:
            u_db = load_json(USER_DB_FILE)      # 加载订阅用户
            d_db = load_json(DEAL_DB_FILE)      # 加载已推送记录
            a_db = load_json(ACTIVITY_DB_FILE)  # 加载用户动态缓存
            page = await context.new_page()
            
            try:
                # --- 部分 A: 自动捡漏监控 ---
                results = await scan_marketplace_v33_original(page)
                print(f"   ∟ 📊 扫描完成，捕获 {len(results)} 张卡牌")
                for item in results:
                    try:
                        pv, fv = float(item['price']), float(item['fmv'])
                        diff = round(fv - pv, 2)
                        
                        # 核心计算逻辑：
                        # 1. FMV < 100 时，差价 >= 5 美元推送
                        # 2. FMV >= 100 时，差价 >= 10 美元推送
                        if (fv < 100 and diff >= 5.0) or (fv >= 100 and diff >= 10.0):
                            # ID+价格作为唯一键，防止价格变动或重复推送
                            if item['id'] and f"{item['id']}_{pv}" not in d_db:
                                d_db[f"{item['id']}_{pv}"] = datetime.now().isoformat()
                                save_json(DEAL_DB_FILE, d_db)
                                
                                print(f"   {GREEN}💰 [发现捡漏] {item['title']} | 利润: ${diff}{RESET}")
                                msg = f"🚨 <b>捡漏播报</b>\n\n卡牌: {item['title']}\n价格: ${pv} | FMV: ${fv}\n利润: <b>${diff}</b>\n\n🔗 <a href='{DETAIL_URL_PREFIX}{item['id']}'>直达详情</a>"
                                # 发送给所有在数据库里的 TG 用户
                                for cid in u_db.keys():
                                    try: await application.bot.send_message(chat_id=cid, text=msg)
                                    except: pass
                    except: continue

                # --- 部分 B: 特定用户 Activity 动态监控 ---
                u_urls = list(set([u for us in u_db.values() for u in us if "/user/" in u]))
                if u_urls:
                    print(f"[{datetime.now().strftime('%H:%M:%S')}] {YELLOW}🕵️ 正在轮询 {len(u_urls)} 用户动态...{RESET}")
                    for t_url in u_urls:
                        uname = t_url.split('/')[-1]
                        try:
                            await page.goto(t_url, wait_until="domcontentloaded", timeout=45000)
                            # 切换到 Activity 选项卡
                            act_tab = page.get_by_text("Activity").first
                            if await act_tab.is_visible():
                                await act_tab.click(force=True)
                                await asyncio.sleep(5)
                                # 抓取最新的活动行
                                acts = await page.evaluate("() => Array.from(document.querySelectorAll('div[role=\"row\"], tr, .Activity_row')).map(r => r.innerText.replace(/\\n/g, ' ').trim()).filter(t => t.length > 30 && !t.includes('Action'))")
                                if acts:
                                    raw_curr = acts[0]
                                    # 过滤掉较旧的记录（天级/月级）
                                    if re.search(r'(\d+\s+days?|months?)\s+ago', raw_curr.lower()): continue
                                    
                                    # 提取地址锚点，用于内容去重，防止因为时间（xx seconds ago）变动导致重复推送
                                    addr_matches = re.findall(r'0x[a-fA-F0-9]+\.\.\.[a-fA-F0-9]+', raw_curr)
                                    if addr_matches:
                                        last_addr = addr_matches[-1]
                                        curr_cleaned = raw_curr[:raw_curr.rfind(last_addr) + len(last_addr)].strip()
                                    else:
                                        curr_cleaned = re.sub(r'\s+(\d+|about|an)\s+(minutes?|hours?|seconds?|ago).*$', '', raw_curr, flags=re.IGNORECASE).strip()

                                    # 对比历史缓存
                                    hist_cleaned = a_db.get(t_url)
                                    if hist_cleaned and curr_cleaned != hist_cleaned:
                                        print(f"   {GREEN}🔔 [新动态] {uname}{RESET}")
                                        m = f"🕵️ <b>用户动态: {uname}</b>\n\n内容：\n<code>{raw_curr}</code>"
                                        for cid in u_db.keys():
                                            try: await application.bot.send_message(chat_id=cid, text=m)
                                            except: pass
                                    a_db[t_url] = curr_cleaned; save_json(ACTIVITY_DB_FILE, a_db)
                        except: continue
            except Exception as e: print(f"❌ 运行异常: {e}")
            finally: await page.close()
            # 轮询间隔
            await asyncio.sleep(REFRESH_INTERVAL)

async def start(u: Update, c: ContextTypes.DEFAULT_TYPE):
    """TG 机器人 /start 命令回复"""
    await u.message.reply_html(
        "🚀 <b>Renaiss 监控系统已连接</b>\n\n"
        "<b>可用命令：</b>\n"
        "/monitor [用户主页链接] - 监控特定用户\n"
        "/list - 查看当前监控列表\n"
        "目前版本: v36.7 (基于 v33 引擎)"
    )

async def post_init(application):
    """程序启动后自动开启监控循环"""
    asyncio.create_task(monitor_loop(application))

if __name__ == "__main__":
    # 初始化 Telegram Bot
    if TG_TOKEN == "在此处填写你的机器人Token":
        print(f"{RED}❌ 请先在脚本中填写 TG_TOKEN！{RESET}")
    else:
        app = ApplicationBuilder().token(TG_TOKEN).defaults(Defaults(parse_mode="HTML")).post_init(post_init).build()
        app.add_handler(CommandHandler("start", start))
        
        # 启动 Bot 轮询
        app.run_polling(drop_pending_updates=True)
