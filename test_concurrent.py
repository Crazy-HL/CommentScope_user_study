import asyncio
from playwright.async_api import async_playwright

async def user_session(p, participant_id, delay):
    """模拟一个用户完成第一篇文章的阅读和答题"""
    await asyncio.sleep(delay)
    browser = await p.chromium.launch(headless=True, executable_path='/Applications/Google Chrome.app/Contents/MacOS/Google Chrome')
    context = await browser.new_context(viewport={'width': 1280, 'height': 800})
    page = await context.new_page()

    print(f"[{participant_id}] 开始实验...")
    await page.goto('http://38.14.249.211', wait_until='networkidle')
    await page.wait_for_timeout(1500)

    # 选择参与者
    await page.evaluate(f"""() => {{
        const sel = document.getElementById('participant-select');
        sel.value = '{participant_id}';
        sel.dispatchEvent(new Event('change', {{bubbles: true}}));
    }}""")
    await page.wait_for_timeout(800)

    # 进入实验
    await page.evaluate("""() => {
        const btns = Array.from(document.querySelectorAll('button'));
        btns.find(b => b.textContent.includes('进入实验'))?.click();
    }""")
    await page.wait_for_timeout(2000)

    # 开始阅读
    await page.evaluate("""() => {
        const btns = Array.from(document.querySelectorAll('button'));
        btns.find(b => b.textContent.includes('开始阅读'))?.click();
    }""")
    await page.wait_for_timeout(2500)

    # 模拟阅读（滚动）
    print(f"[{participant_id}] 阅读中...")
    for i in range(3):
        await page.evaluate(f"window.scrollTo(0, document.body.scrollHeight * {0.3 * (i+1)})")
        await page.wait_for_timeout(500)

    # 完成阅读
    await page.evaluate("window.scrollTo(0, 0)")
    await page.wait_for_timeout(500)
    await page.evaluate("""() => {
        const btns = Array.from(document.querySelectorAll('button'));
        btns.find(b => b.textContent.includes('完成阅读并答题'))?.click();
    }""")
    await page.wait_for_timeout(1200)
    await page.evaluate("""() => {
        const btns = Array.from(document.querySelectorAll('button'));
        btns.find(b => b.textContent.includes('确认'))?.click();
    }""")
    await page.wait_for_timeout(1500)

    # 完成10道题
    print(f"[{participant_id}] 答题中...")
    for q in range(12):
        await page.evaluate("""() => {
            const btns = Array.from(document.querySelectorAll('button'));
            btns.find(b => b.textContent.includes('开始答题'))?.click();
        }""")
        await page.wait_for_timeout(400)
        # 随机选择选项（不是每次都选第一个，模拟真实答题）
        await page.evaluate("""() => {
            const opts = document.querySelectorAll('.option, label.option, [class*="option"]');
            if (opts.length > 0) {
                const idx = Math.floor(Math.random() * opts.length);
                opts[idx].click();
            }
        }""")
        await page.wait_for_timeout(300)
        await page.evaluate("""() => {
            const btns = Array.from(document.querySelectorAll('button'));
            btns.find(b => b.textContent.includes('提交答案') || b.textContent.includes('下一题'))?.click();
        }""")
        await page.wait_for_timeout(500)

        # 检查是否到了 NASA-TLX
        has_slider = await page.evaluate("() => document.querySelectorAll('input[type=\"range\"]').length > 0")
        if has_slider:
            print(f"[{participant_id}] 第{q+1}题后到达评价页面")
            break

    await page.wait_for_timeout(1000)

    # NASA-TLX 评价
    try:
        await page.wait_for_selector("input[type='range']", timeout=8000)
        await page.evaluate("""() => {
            document.querySelectorAll('input[type="range"]').forEach(s => {
                s.value = Math.floor(Math.random() * 7) + 1;
                s.dispatchEvent(new Event('input', {bubbles: true}));
                s.dispatchEvent(new Event('change', {bubbles: true}));
            });
            document.querySelectorAll('select').forEach(sel => {
                const opts = Array.from(sel.options).filter(o => o.value);
                if (opts.length > 0) {
                    const opt = opts[Math.floor(Math.random() * opts.length)];
                    sel.value = opt.value;
                    sel.dispatchEvent(new Event('change', {bubbles: true}));
                }
            });
        }""")
        await page.wait_for_timeout(400)
        await page.evaluate("""() => {
            const btns = Array.from(document.querySelectorAll('button'));
            btns.find(b => b.textContent.includes('提交评价') || b.textContent.includes('提交'))?.click();
        }""")
        print(f"[{participant_id}] NASA-TLX 已提交")
        await page.wait_for_timeout(2000)
    except Exception as e:
        print(f"[{participant_id}] NASA-TLX 异常: {e}")

    print(f"[{participant_id}] 第一篇文章完成！")
    await browser.close()
    return participant_id

async def main():
    async with async_playwright() as p:
        # 两个用户同时开始（错开2秒）
        results = await asyncio.gather(
            user_session(p, 'P16', 0),
            user_session(p, 'P17', 2)
        )
        print(f"\n测试完成: {results}")

asyncio.run(main())
