# tornado-mongo-seed

基于 Python3 + Tornado + MongoDB 的Web后端项目模板。

可以基于此项目替换：
- tornado-mongo-seed 项目名
- 默认端口号 8001
- seed_main.py 文件名
- _app.yml 中的数据库名和网站名

## 安装

本平台需要 Python 3.6+、MongoDB，请参考下面的说明安装和部署。

- [INSTALL-linux.md](doc/INSTALL-linux.md)
- [INSTALL-mac.md](doc/INSTALL-mac.md)
- [INSTALL-win.md](doc/INSTALL-win.md)

## 测试

本项目可采用测试驱动开发(TDD)模式实现后端接口：

```
pip3 install -r tests/requirements.txt
python3 run_tests.py 或选中测试用例文件调试
```

在 `tests` 下编写测试用例，然后在 `controller` 下实现后端接口。

如果需要单独多次调试某个用例，可将 `run_tests.py` 中的 `test_args += ['-k test_` 行注释去掉，
改为相应的测试用例名，在用例或API响应类中设置断点调试。

## 参考资料

- [Tornado 官方文档中文版](https://tornado-zh.readthedocs.io/zh/latest/)
- [MongoDB 数据库开发](http://demo.pythoner.com/itt2zh/ch4.html)
- [MongoDB 官方文档](http://api.mongodb.com/python/current/index.html)
- [MongoDB 查询操作符](https://docs.mongodb.com/manual/reference/operator/query/)
