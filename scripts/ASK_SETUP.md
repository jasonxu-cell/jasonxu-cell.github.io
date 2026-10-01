# 匿名提问箱

页面是 `ask.html`，全站导航中的 **Ask** 可进入。访客只需填写问题，不需要姓名、邮箱或登录；未回答的问题不会出现在公开页面上。

## 接收问题

1. 登录 [Formspree](https://formspree.io/)，创建一个表单，例如“匿名提问箱”。
2. 打开表单的 **Integration** 标签，复制 **Your form's endpoint is** 下的地址。
3. 将 `scripts/ask.js` 开头的 `FORM_ENDPOINT` 设置成这个地址：

   ```js
   var FORM_ENDPOINT = "https://formspree.io/f/你的表单ID";
   ```

4. 更新 `ask.html` 中 `scripts/ask.js?v=` 的版本参数（例如当前日期），然后部署网站。
5. 从网站发送一条测试问题，在 Formspree 后台确认收到。接收邮箱和通知可在 Formspree 中配置。

地址未配置时，页面会显示尚未开放，发送按钮禁用。超时或发送失败会保留问题内容。前端包含 Formspree 的 `_gotcha` 蜜罐字段；额外防刷功能需在服务端配置。

表单地址可以公开放在网站代码中，不要填入账号密码、API 密钥或后台地址。

## 发布回答

在 `scripts/ask.js` 的 `QA` 数组里添加：

```js
{
    question: "收到的问题",
    answer: "你的回答。\n\n第二段回答。",
    date: "2026-09-30"
},
```

按日期从新到旧显示，文本会转义，答案可以包含换行。`template: true` 的示例只会在 `ask.html?preview` 显示，不会当成真实问答公开。

参考：[Formspree 表单地址说明](https://help.formspree.io/articles/the-forms-api/getting-your-form-s-hashid)。
