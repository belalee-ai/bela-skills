# JS 数据提取模板

用于新的浏览器自动化路由：优先通过 `bb-browser eval` 在已登录的小红书页面执行 JS 提取 SSR 数据；普通无登录态页面可用 `agent-browser eval`。不要再使用 `web-access` 或旧的 `javascript_tool` 调用链。

## 笔记详情页提取

在笔记详情页执行，提取笔记数据和评论：

```javascript
(function(){
    var s=window.__INITIAL_STATE__;
    var m=(s.note||{}).noteDetailMap||{};
    for(var k in m){
        var n=m[k].note||{};var u=n.user||{};var i=n.interactInfo||{};
        var noteData={noteId:k,title:n.title||'',desc:n.desc||'',type:n.type||'',
            likes:i.likedCount||'',comments:i.commentCount||'',collects:i.collectedCount||'',
            shares:i.shareCount||'',tags:(n.tagList||[]).map(function(t){return t.name||''}),
            author:{nickname:u.nickname||'',userId:u.userId||''}};
        var list=(m[k].comments||{}).list||[];var cs=[];
        if(Array.isArray(list)){list.forEach(function(c){
            if(c.content)cs.push({content:c.content,likes:c.likeCount||0,nickname:(c.userInfo||{}).nickname||''});
            (c.subComments||[]).forEach(function(sc){
                if(sc.content)cs.push({content:sc.content,likes:sc.likeCount||0,nickname:(sc.userInfo||{}).nickname||''});
            });
        });}
        noteData.comment_list=cs;
        return JSON.stringify(noteData,null,2);
    }
})()
```

## 博主主页提取

在博主主页执行，提取作者信息和笔记列表：

```javascript
(function(){
    var s=window.__INITIAL_STATE__;
    var ud=(s.user||{}).userPageData||{};var b=ud.basicInfo||{};
    var userInfo={nickname:b.nickname||'',desc:b.desc||'',ip:b.ipLocation||'',redId:b.redId||''};
    var notes_raw=(s.user||{}).notes||[];
    if(notes_raw.length&&Array.isArray(notes_raw[0]))notes_raw=notes_raw[0];
    var notes=notes_raw.map(function(n){var c=n.noteCard||{};var i=c.interactInfo||{};
        return{title:c.displayTitle||'',type:c.type||'',likes:i.likedCount||'',
            sticky:i.sticky||false,noteId:c.noteId||n.id||'',xsecToken:c.xsecToken||''};
    });
    return JSON.stringify({user:userInfo,notes:notes},null,2);
})()
```
