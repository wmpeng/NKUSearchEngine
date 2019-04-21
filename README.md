# NKUSearchEngine

`NKUSearchEngine`为搜索引擎后端，其中`spider`为爬虫部分，`search-engine`为索引及搜索部分。`NKUSearchEngineFrontend`（<https://github.com/wmpeng/NKUSearchEngineFrontend/>）为搜索引擎前端。

# spider

## 目录结构

```tree
.
│  myparser.py
│  mytool.py
│  redis_access.py
│  spider.py
│
└─config
       config.json
       local-config.json
       secret-config.json
```

`myparse.py`: 有关html的解析。

`mytool.py`：有关读取配置文件的方法和其他静态的常用方法，包括其他调试用的函数。

`redis_access.py`：直接读取`redis`的类`MyRedisAccessor`，和`redis`有关的操作的类`MyRedisUtil`。

`spider.py`：和爬虫相关的所有内容。

`config/config.json`：默认的配置文件，在之后的部分中有介绍。

`config/local-config.json`：本地配置相关的文件，如路径及其他对`config.json`的覆盖。这个文件需要手动创建。

`config/secret-config.json`：和服务器主机地址、端口及密码相关的配置。这个文件需要手动创建。

## 依赖项

1. `redis`：存储当前爬取包括已爬取和带爬取的url，过期时间等。
2. `http_proxy`：因为部分网站有访问限制，如果配置在校外部分网页会有`http 403 forbidden`错误。
3. `python3`：spider为python3项目，经过python3.7环境下测试。
4. `chrome`或`chromium`：作为无头（heedless）浏览器用于解析动态网页。在`Chromium 73.0.3683.86`测试。
5. `chrome webdriver`：用作操作`chrome`，在`73.0.3683.68`（<https://chromedriver.storage.googleapis.com/73.0.3683.68/>）测试。

## config 文件

请创建`spider/local-config.json`和`spider/secret-config.json`文件，按照我们的设计，对于默认`config.json`的修改都是使用在`local-config.json`或`secret-config.json`中覆盖的方式。在`local-config.json`中修改`path`的绝对路径，在`secret-config.json`中配置各个服务的`host`和`port`。

### `config.json`

| Key                                 | Type           | Description                                                                |
| ----------------------------------- | -------------- | -------------------------------------------------------------------------- |
| path.document                       | string         | 存储爬取内容的解析结果的文件夹的绝对路径                                   |
| path.page                           | string         | 存储爬取内容原始格式的文件夹的绝对路径                                     |
| path.log                            | string         | 日志文件夹                                                                 |
| path.download_temp_dir              | string         | 用作下载时充当临时目录的目录                                               |
| spider.valid_url                    | regular string | 表示允许的url格式，用来限制只爬取内网                                      |
| spider.invalid_url                  | regular string | 表示不进行爬取的url格式，满足valid_url并且不满足invalid_url的url才会被爬取 |
| spider.invalid_file_type            | string         | 排除的爬取类型                                                             |
| spider.browser_user_agent           | string         | 爬取时使用的user_agent                                                     |
| spider.urlopen_timeout              | float          | 使用urllib爬取时的超时                                                     |
| spider.driver.wait_download_max_sec | float          | 使用浏览器下载文件时的超市                                                 |
| spider.driver.page_load_timeout     | float          | 使用浏览器时的page_load_timeout                                            |
| spider.driver.script_timeout        | float          | 使用浏览器时的script_timeout                                               |
| spider.browser                      | string         | 使用的无头浏览器firfox或chrome                                             |
| spider.proxy_type                   | string         | proxy类型，目前只支持http                                                  |
| spider.proxy_url                    | string         | proxy的主机和端口，"no_host"表示不使用代理，如"127.0.0.1:8123"             |
| redis.host                          | string         | redis的host                                                                |
| redis.port                          | integer        | redis的port                                                                |
| job.default_interval                | integer        | 表示一个新的url默认的更新间隔                                              |
| job.min_interval                    | integer        | 表示一个url最小的更新间隔                                                  |
| job.max_interval                    | integer        | 表示一个url最大的更新间隔                                                  |
| job.start_url                       | string         | 表示爬虫开始的url                                                          |

### `local-config.json` 和 `secret-config.json` 的例子：

* local-config.json

```json
{
  "path.document" : "/root/NKUSearchEngine/documents/",
  "path.page" : "/root/NKUSearchEngine/pages/",
  "path.log" : "/root/NKUSearchEngine/logs/spider/",
  "path.download_temp_dir": "/root/NKUSearchEngine/downloads/",

  "spider.browser": "firefox",

  "job.default_interval": 864000,
  "job.start_url": "http://cc.nankai.edu.cn"
}
```

* secret-config.json

```json
{
  "redis.host": "127.0.0.1",
  "redis.port": 6379,

  "spider.proxy_url":"127.0.0.1:1080"
}
```

## 使用

```bash
python spider job_type max_doc_num

example:
python spider new_job 100
```

`max_doc_num`指本次最多爬取多少个url。

`job_type`是任务类型，包括`new_job`，`resume`和`new_batch`。
`new_job`是指开始一个新的爬虫，对应的是`job.start_url`。
`new_batch`指的是对于这个`job.start_url`的一次增量爬虫。
`resume`是继续之前由于达到`max_doc_num`而结束或者由于`KeyboardInterrupt`而结束的爬虫。

# search-engine

## 目录结构

```tree
.
│  pom.xml
│  search-engine.iml
│
├─src
│  ├─main
│  │  ├─bin
│  │  │      package.bat
│  │  │      package.sh
│  │  │
│  │  ├─java
│  │  │  ├─common
│  │  │  │      Util.java
│  │  │  │
│  │  │  ├─redis
│  │  │  │      RedisAccess.java
│  │  │  │
│  │  │  └─retrieval
│  │  │          Index.java
│  │  │          Main.java
│  │  │          Search.java
│  │  │          SearchServer.java
│  │  │
│  │  └─resources
│  │      └─config
│  │         ├─dev
│  │         │      config.json
│  │         │      local-config.json
│  │         │      secret-config.json
│  │         │
│  │         └─prod
│  │                 config.json
│  │                 local-config.json
│  │                 secret-config.json
│  │
│  └─test
│      └─java
│          ├─common
│          │      UtilTest.java
│          │
│          ├─redis
│          │      RedisAccessTest.java
│          │
│          └─retrieval
│                  IndexTest.java
│                  SearchServerTest.java
│                  SearchTest.java
│
└─target
```

* `search-engine.iml`：工程配置文件。
* `pom.xml`：Maven的配置文件。
* `src/main`：所有的源文件及资源目录。
  * `src/main/bin`：用于生成`jar`的脚本。
  * `src/java`：源文件目录。
    * `src/java/common`：项目中公用的代码，主要是读取配置文件的类。
    * `src/java/redis`：和访问redis相关的类。
    * `src/java/retrieval`：主要部分的目录，包括建立索引和搜索
      * `Index.java`：建立索引的类。
      * `Search.java`：搜索相关的类。
      * `SearchServer.java`：简历一个搜索服务，等待前端发送查询字符串，并调用`Search`之后返回查询结果。
      * `Main.java`：主类，用于根据参数调用`Index`或`SearchServer`。
  * `src/resources`：资源文件目录。
    * `src/resources/config`：配置文件夹，下面有对应的不同environment的文件夹
      * `src/resources/config/dev`：develop环境的配置文件
      * `src/resources/config/prod`：product环境的配置文件
* `src/test`：测试的源文件，目录结构和`src/main`源码部分相对应。
* `target/`：目标文件夹，jar包生成在这个目录。

## search-engine 依赖项

1. `jdk8+`：在`openjdk 1.8.0_191`和`Oracle JDK 11.0.2`测试运行。
2. `maven3`：在`maven 3.3.9`测试运行。

## config 文件

| Key                   | Type    | Description                              |
| --------------------- | ------- | ---------------------------------------- |
| path.document         | string  | 存储爬取内容的解析结果的文件夹的绝对路径 |
| path.index            | string  | 建立索引的文件夹                         |
| redis.host            | string  | redis的host                              |
| redis.port            | integer | redis的port                              |
| search.top_k          | integer | 对于每个查询默认返回的文档个数           |
| search.snippet_length | integer | 摘要的默认长度                           |
| search_server.host    | string  | searchServer的host                       |
| search_server.port    | string  | searchServer的端口                       |

## 使用

```bash
java -jar search-engine-{version}-jar-with-dependencies.jar env job_type

example:
java -jar search-engine-0.1-jar-with-dependencies.jar prod index
```

`env`可选`dev`和`prod`，使用对应的配置文件。
`job_type`可选`index`和`server`，分别表示建立索引和开始监听查询。每次爬取之后要重新建立索引才能使用新的文档。
