# 三步完成 GitHub 发布

## 📋 步骤 1：创建 GitHub 仓库

1. 访问：https://github.com/new
2. **Repository name**: `sansheng`
3. **Description**: 基于 OpenClaw 的多 Agent 协作框架，模拟古代三省六部制决策流程
4. **Visibility**: ✅ Public (公开)
5. **不要勾选** "Add a README file" / "Add .gitignore" / "Choose a license"
6. 点击 **"Create repository"**

---

## 📋 步骤 2：复制推送命令

创建完成后，GitHub 会显示推送指令。复制类似以下的命令：

```bash
git remote add origin git@github.com:xusongquan-evil/sansheng.git
git branch -M main
git push -u origin main
```

---

## 📋 步骤 3：在服务器上执行

在你的服务器上执行：

```bash
cd /root/.openclaw/workspace/sansheng-github
git remote add origin git@github.com:xusongquan-evil/sansheng.git
git branch -M main
git push -u origin main
```

---

## ✅ 完成！

推送成功后，访问：https://github.com/xusongquan-evil/sansheng

---

## 🎉 后续优化

### 1. 添加 GitHub Topics
在仓库页面点击 "Manage topics"，添加：
- `openclaw`
- `multi-agent`
- `ai`
- `automation`
- `workflow`
- `china`

### 2. 完善 README
可以考虑添加：
- 架构图/流程图
- 实际运行截图
- 更多示例任务

### 3. 添加 GitHub Actions
创建 `.github/workflows/test.yml` 自动测试 CLI 工具

---

**需要我帮你执行步骤 3 的推送命令吗？** 创建好仓库后告诉我！
