# 项目介绍
这是一个Web爬虫项目，从cook目录下各个菜品的markdown文件提取菜品名，进入百度百科搜索并抓取该菜品的介绍信息，补充到对应的markdown文件中。

## 技术和环境
开发语言：Python 3.14
虚拟环境：web_crawler
Python库：
- cloudscraper：绕过 Cloudflare/百度反爬验证
- BeautifulSoup4：HTML解析利器
- lxml：高性能解析器
项目目录：~/Workspace/web_crawler/cook_baidu_baike

## 安装依赖
```bash
# 创建并激活虚拟环境
python3 -m venv ~/Workspace/web_crawler/web_crawler
source ~/Workspace/web_crawler/web_crawler/bin/activate

# 安装依赖
pip install cloudscraper beautifulsoup4 lxml
```

## 运行爬虫
```bash
source ~/Workspace/web_crawler/web_crawler/bin/activate
cd ~/Workspace/web_crawler/cook_baidu_baike
python3 crawler.py
```

## 开发流程
**初始化**
爬虫初始化配置：
- 百度百科 URL: https://baike.baidu.com/item/{}
- cloudscraper 实例（复用，模拟 Chrome 浏览器行为）
- 爬取间隔 Delay：1s（加上 0.5-2s 随机浮动）
- 超时时间 TimeOut：15s
- 最大重试次数：3

**提取菜品名**
递归遍历 `cook/dishes/` 目录下所有子目录，收集 `.md` 文件，使用文件名的非后缀部分作为菜品名。

**百度百科搜索菜品**
通过百度百科 URL 搜索菜品对应的词条，提取词条摘要（class="J-summary"）。

**更新菜品 md 文件**
将摘要信息以 `# <菜品名>的介绍` 格式添加到 md 文件头部，其余内容保持不变。
如果文件已包含介绍则跳过。
如果无法获取词条（404）、摘要为空或请求异常，跳过该菜品。

## 反爬策略
百度百科的反爬机制及应对：
1. User-Agent 验证 → cloudscraper 动态生成浏览器指纹
2. JS 安全验证 → cloudscraper 自动解析 JS 挑战
3. 高频访问限制 → 每次请求间隔 1.5-3s 随机延迟
4. 异常重试 → 最多重试 3 次，间隔递增

## 实现效果
运行 `crawler.py` 处理 `cook/dishes/` 目录下全部 323 个菜品文件，结果如下：

- ✅ **成功写入 23 个**：获取到百度百科词条摘要，已写入文件头部
- ❌ **跳过 300 个**：原因包括无词条（404）、反爬拦截（403）等

### 写入格式示例
以水煮鱼为例，爬虫在 `水煮鱼.md` 文件头部插入的百科介绍：

```markdown
# 水煮鱼的介绍
水煮鱼又称江水煮江鱼、水煮鱼片，是中国川渝地区的一道特色名菜，属于川菜系，其最早流行于重庆市渝北区翠云乡。
水煮鱼通常由新鲜草鱼、豆芽、辣椒等食材制作而成。"油而不腻、辣而不燥、麻而不苦、肉质滑嫩"是其特色。

# 水煮鱼的做法
...（原有内容保持不变）
```

### 失败原因分析
后期待请求量增大后，百度百科开始频繁返回 403（反爬拦截），导致后续 300 个菜品未能成功抓取。尝试以下优化策略后依然会被反爬拦截，下个版本会通过百度百科的API获取词条摘要信息：
- 增大请求间隔（建议 5-10 秒以上）
- 每次请求新建 cloudscraper 实例，避免 session 被标记
- 分批运行，每批之间有足够冷却时间
- 使用代理 IP 池轮换
