# AnJianJingLing
python实现的按键精灵
目前鼠标的移动和点击 相对比较好
键盘单独的响应也可以
鼠标和键盘的配合不好，因为他们两个是单独的线程，放映的时候也是单独进行放映 。之后可以考虑把他们放在一个线程 或者每一个保存的内容里边加上时间控制（或者用一个动作的全局变量也可以）
