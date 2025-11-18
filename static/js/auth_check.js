// 通用的认证检查脚本
(function() {
    const token = localStorage.getItem('token');
    const user = JSON.parse(localStorage.getItem('user') || '{}');
    
    if (!token) {
        // 没有token，跳转到登录
        alert('Please login first');
        window.location.href = '/login';
        return;
    }
    
    if (user.role !== 'patient') {
        // 不是患者角色
        alert('This page is for patients only');
        window.location.href = '/login';
        return;
    }
    
    // Token存在且是患者，允许访问
    console.log('Authenticated as:', user.username);
})();