## contype 和 conaffinity 决定哪些几何可以碰撞

`contype` 表示几何属于哪些碰撞类别，`conaffinity` 表示它接受哪些类别。自动配对时，只要一侧 `contype` 和对侧 `conaffinity` 按位与非零，就过了掩码这一关。还要核对碰撞开关、body 排除和父子过滤。显式 `contact/pair` 走单独的配对路径。

如果指腹接近物体却始终找不到目标接触，固定一个两碰撞表面确实相交的姿态，在 `data.contact` 里查这对 geom。仍无记录时，优先查碰撞过滤。如果只有高速运动时漏掉，比较更小步长下的几何距离和首次接触时刻。

{ref}`按现象查接触参数 <contact-tuning>`
