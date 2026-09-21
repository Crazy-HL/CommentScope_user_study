import asyncio
import os
from playwright.async_api import async_playwright

OUTPUT_DIR = "/Users/hl/Desktop/Comments_Annotations/TC_Enhancement-main/wikitable-vue/screenshots"
BASE_URL = "http://38.14.249.211"
CHROME_PATH = "/Applications/Google Chrome.app/Contents/MacOS/Google Chrome"

async def click_any(page, texts, timeout=4000):
    """尝试点击包含任意指定文本的按钮"""
    for text in texts:
        try:
            btn = page.locator(f"button:has-text('{text}')")
            if await btn.count() > 0:
                await btn.first.click(timeout=timeout)
                return True
        except:
            pass
    try:
        await page.evaluate(f"""() => {{
            const btns = Array.from(document.querySelectorAll('button'));
            const btn = btns.find(b => { ' || '.join([f"b.textContent.includes('{t}')" for t in texts]) }));
            if (btn) btn.click();
        }}""")
        return True
    except:
        return False

async def finish_current_article(page):
    """快速完成当前文章的所有答题和评价"""
    # 点击完成阅读
    await click_any(page, ["完成阅读并答题", "完成阅读", "开始答题"])
    await page.wait_for_timeout(800)
    await click_any(page, ["确认", "确定", "完成"])
    await page.wait_for_timeout(1000)

    # 完成4类题目（CRA 4 + ACA 2 + CTIA 2 + Location 2 = 10题）
    for _ in range(12):  # 多给几次机会
        try:
            # 点击开始答题
            await click_any(page, ["开始答题"], timeout=2000)
            await page.wait_for_timeout(500)
            # 选择第一个选项
            await page.evaluate("""() => {
                const opts = document.querySelectorAll('.option, label.option, [class*="option"], label');
                if (opts.length > 0) opts[0].click();
            }""")
            await page.wait_for_timeout(200)
            # 提交
            await click_any(page, ["提交答案", "下一题", "提交"], timeout=2000)
            await page.wait_for_timeout(600)
        except:
            break

    await page.wait_for_timeout(1500)

    # NASA-TLX 评价：设置所有滑块为中间值并提交
    try:
        await page.evaluate("""() => {
            const sliders = document.querySelectorAll('input[type="range"]');
            sliders.forEach(s => {
                s.value = 4;
                s.dispatchEvent(new Event('input', {bubbles: true}));
                s.dispatchEvent(new Event('change', {bubbles: true}));
            });
        }""")
        await page.wait_for_timeout(300)
        await click_any(page, ["提交", "下一篇", "完成"], timeout=3000)
        await page.wait_for_timeout(2000)
    except:
        pass

async def main():
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True, executable_path=CHROME_PATH)
        context = await browser.new_context(viewport={"width": 1440, "height": 900}, locale="zh-CN")
        page = await context.new_page()

        # 打开实验入口
        await page.goto(BASE_URL, wait_until="networkidle")
        await page.wait_for_timeout(1500)

        # 选择 G3 组的参与者（P13-P18），界面顺序：01=SE, 02=BL, 03=TE, 04=CS
        chosen = await page.evaluate("""() => {
            const sel = document.getElementById('participant-select');
            if (!sel) return null;
            // 优先选 P13-P18
            const preferred = ['P13','P14','P15','P16','P17','P18'];
            for (const val of preferred) {
                const opt = Array.from(sel.options).find(o => o.value === val && !o.disabled);
                if (opt) {
                    sel.value = val;
                    sel.dispatchEvent(new Event('change', {bubbles: true}));
                    return val;
                }
            }
            // 退而求其次选任意可用的
            const opts = Array.from(sel.options).filter(o => o.value && !o.disabled);
            if (opts.length > 0) {
                sel.value = opts[0].value;
                sel.dispatchEvent(new Event('change', {bubbles: true}));
                return opts[0].value;
            }
            return null;
        }""")
        print(f"选择参与者: {chosen}")
        await page.wait_for_timeout(800)
        await click_any(page, ["进入实验", "进入"])
        await page.wait_for_timeout(2000)

        # 实验说明 - 开始
        await click_any(page, ["开始阅读", "开始实验", "开始"])
        await page.wait_for_timeout(2500)

        # 4篇文章的界面名称（G3组：SE, BL, TE, CS）
        article_interfaces = ["SE", "BL", "TE", "CS"]
        article_nums = ["01", "02", "03", "04"]

        for i in range(4):
            print(f"\n=== 文章 {article_nums[i]}（{article_interfaces[i]} 界面）===")
            await page.wait_for_timeout(1500)

            # 截取阅读界面（顶部+文章内容）
            await page.evaluate("window.scrollTo(0, 0)")
            await page.wait_for_timeout(500)
            screenshot_file = f"article_{article_nums[i]}_{article_interfaces[i]}.png"
            await page.screenshot(path=f"{OUTPUT_DIR}/{screenshot_file}", full_page=False)
            print(f"  截图: {screenshot_file}")

            # 截取文章中间部分（展示评论嵌入效果）
            await page.evaluate("window.scrollTo(0, document.body.scrollHeight * 0.35)")
            await page.wait_for_timeout(800)
            mid_file = f"article_{article_nums[i]}_{article_interfaces[i]}_mid.png"
            await page.screenshot(path=f"{OUTPUT_DIR}/{mid_file}", full_page=False)
            print(f"  截图: {mid_file}")

            # 如果不是最后一篇，完成当前文章进入下一篇
            if i < 3:
                print("  快速完成当前文章...")
                await finish_current_article(page)
                # 下一篇文章的实验说明/开始
                await click_any(page, ["开始阅读", "开始实验", "开始"])
                await page.wait_for_timeout(2000)

        await browser.close()
        print("\n完成！4篇文章阅读界面截图已保存。")

if __name__ == "__main__":
    asyncio.run(main())
