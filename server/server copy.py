# server.py
import tornado.ioloop
import tornado.web
import json
import jieba
import jieba.analyse
from collections import defaultdict
import os

# 初始化jieba
jieba.initialize()

# 创建停用词集合
stopwords = set([
    '的', '了', '和', '是', '就', '都', '而', '及', '與', '著', '或', 
    '一个', '没有', '我们', '你们', '他们', '这个', '那个', '在', '有',
    '要', '也', '会', '可以', '可能', '我', '你', '他', '她', '它',
    '这', '那', '这些', '那些', '什么', '怎么', '为什么', '如何',
    '很', '非常', '太', '更', '最', '比较', '一些', '一点', '许多'
])

class ArticleHandler(tornado.web.RequestHandler):
    def set_default_headers(self):
        self.set_header("Access-Control-Allow-Origin", "*")
        self.set_header("Access-Control-Allow-Headers", "Content-Type")
        self.set_header("Access-Control-Allow-Methods", "GET, POST, OPTIONS")
    
    def options(self):
        self.set_status(204)
        self.finish()
    
    def get(self):
        try:
            with open('content.json', 'r', encoding='utf-8') as f:
                data = json.load(f)
                self.write(json.dumps(data, ensure_ascii=False))
        except FileNotFoundError:
            self.set_status(404)
            self.write(json.dumps({"error": "Article not found"}))
        except Exception as e:
            self.set_status(500)
            self.write(json.dumps({"error": str(e)}))

# class CommentsHandler(tornado.web.RequestHandler):
#     def set_default_headers(self):
#         self.set_header("Access-Control-Allow-Origin", "*")
#         self.set_header("Access-Control-Allow-Headers", "Content-Type")
#         self.set_header("Access-Control-Allow-Methods", "GET, POST, OPTIONS")
    
#     def options(self):
#         self.set_status(204)
#         self.finish()
    
#     def get(self):
#         try:
#             with open('comments.json', 'r', encoding='utf-8') as f:
#                 comments = json.load(f)
                
#                 # 预处理高频词
#                 sentence_comments = defaultdict(list)
#                 for comment in comments:
#                     if isinstance(comment, dict) and 'link' in comment and 'content' in comment:
#                         sentence_comments[comment['link']].append(comment['content'])
                
#                 # 分析每个句子的高频词
#                 high_freq_words = {}
#                 for sentence_id, comment_list in sentence_comments.items():
#                     if sentence_id == -1:  # 跳过全局评论
#                         continue
                    
#                     # 合并所有评论内容
#                     combined_text = ' '.join(comment_list)
                    
#                     # 使用jieba提取关键词（带权重）
#                     keywords = jieba.analyse.extract_tags(
#                         combined_text, 
#                         topK=5,  # 提取前5个关键词
#                         withWeight=True,  # 返回权重
#                         allowPOS=('n', 'vn', 'v', 'a')  # 只提取名词、动名词、动词和形容词
#                     )
                    
#                     # 过滤停用词
#                     filtered_keywords = [
#                         (word, weight) for word, weight in keywords 
#                         if word not in stopwords and len(word) > 1
#                     ]
                    
#                     high_freq_words[sentence_id] = filtered_keywords[:3]  # 只保留前3个
                
#                 # 将高频词信息添加到返回数据中
#                 result = {
#                     'comments': comments,
#                     'high_freq_words': high_freq_words
#                 }
#                 self.write(json.dumps(result, ensure_ascii=False))
#         except FileNotFoundError:
#             self.set_status(404)
#             self.write(json.dumps({"error": "Comments not found"}))
#         except Exception as e:
#             self.set_status(500)
#             self.write(json.dumps({"error": str(e)}))

class CommentsHandler(tornado.web.RequestHandler):
    def set_default_headers(self):
        self.set_header("Access-Control-Allow-Origin", "*")
        self.set_header("Access-Control-Allow-Headers", "Content-Type")
        self.set_header("Access-Control-Allow-Methods", "GET, POST, OPTIONS")
    
    def options(self):
        self.set_status(204)
        self.finish()
    
    def get(self):
        try:
            with open('comments.json', 'r', encoding='utf-8') as f:
                comments = json.load(f)
                
                # 预处理高频词
                sentence_comments = defaultdict(list)
                for comment in comments:
                    if isinstance(comment, dict) and 'link' in comment and 'content' in comment:
                        # 处理link字段可能是数组或数字的情况
                        links = comment['link']
                        if isinstance(links, list):
                            for link in links:
                                if link != -1:  # 跳过全局评论
                                    sentence_comments[link].append(comment['content'])
                        else:
                            if links != -1:  # 跳过全局评论
                                sentence_comments[links].append(comment['content'])
                
                # 分析每个句子的高频词
                high_freq_words = {}
                for sentence_id, comment_list in sentence_comments.items():
                    # 合并所有评论内容
                    combined_text = ' '.join(comment_list)
                    
                    # 使用jieba提取关键词（带权重）
                    try:
                        keywords = jieba.analyse.extract_tags(
                            combined_text, 
                            topK=5,  # 提取前5个关键词
                            withWeight=True,  # 返回权重
                            allowPOS=('n', 'vn', 'v', 'a')  # 只提取名词、动名词、动词和形容词
                        )
                        
                        # 过滤停用词
                        filtered_keywords = [
                            (word, weight) for word, weight in keywords 
                            if word not in stopwords and len(word) > 1
                        ]
                        
                        high_freq_words[sentence_id] = filtered_keywords[:3]  # 只保留前3个
                    except Exception as e:
                        print(f"Error processing sentence {sentence_id}: {e}")
                        high_freq_words[sentence_id] = []
                
                # 将高频词信息添加到返回数据中
                result = {
                    'comments': comments,
                    'high_freq_words': high_freq_words
                }
                self.write(json.dumps(result, ensure_ascii=False))
        except FileNotFoundError:
            self.set_status(404)
            self.write(json.dumps({"error": "Comments not found"}))
        except Exception as e:
            print(f"Error in CommentsHandler: {e}")  # 添加错误日志
            self.set_status(500)
            self.write(json.dumps({"error": str(e)}))
            
class SentenceHandler(tornado.web.RequestHandler):
    def set_default_headers(self):
        self.set_header("Access-Control-Allow-Origin", "*")
        self.set_header("Access-Control-Allow-Headers", "Content-Type")
        self.set_header("Access-Control-Allow-Methods", "POST, OPTIONS")
    
    def options(self):
        self.set_status(204)
        self.finish()
    
    def post(self):
        try:
            data = json.loads(self.request.body)
            sentence = data.get('sentence', '')
            
            if not sentence:
                self.set_status(400)
                self.write(json.dumps({"error": "Empty sentence"}))
                return
            
            # 分词
            words = list(jieba.cut(sentence))
            
            # 提取关键词
            keywords = jieba.analyse.extract_tags(
                sentence,
                topK=3,
                withWeight=True,
                allowPOS=('n', 'vn', 'v', 'a')
            )
            
            # 过滤停用词
            filtered_keywords = [
                (word, weight) for word, weight in keywords 
                if word not in stopwords and len(word) > 1
            ]
            
            result = {
                'words': words,
                'keywords': filtered_keywords
            }
            self.write(json.dumps(result, ensure_ascii=False))
        except json.JSONDecodeError:
            self.set_status(400)
            self.write(json.dumps({"error": "Invalid JSON"}))
        except Exception as e:
            self.set_status(500)
            self.write(json.dumps({"error": str(e)}))

def make_app():
    return tornado.web.Application([
        (r"/article", ArticleHandler),
        (r"/comments", CommentsHandler),
        (r"/analyze-sentence", SentenceHandler),
    ], debug=True)

if __name__ == "__main__":
    app = make_app()
    port = int(os.environ.get("PORT", 8888))
    app.listen(port)
    print(f"Server is running on http://localhost:{port}")
    tornado.ioloop.IOLoop.current().start()