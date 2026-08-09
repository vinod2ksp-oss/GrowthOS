import { expect, test } from '@playwright/test';

test('completed task flows through inventory review adjustment and next plan', async ({ page }) => {
  const email = `phase3-${Date.now()}@example.com`;
  await page.goto('/register');
  await page.getByPlaceholder('邮箱').fill(email);
  await page.getByPlaceholder('密码').fill('secret123');
  await page.getByRole('button', { name: '注册' }).click();
  await expect(page).toHaveURL(/\/login/);
  await page.getByPlaceholder('邮箱').fill(email);
  await page.getByPlaceholder('密码').fill('secret123');
  await page.getByRole('button', { name: '登录' }).click();
  await page.getByPlaceholder('昵称').fill('Phase 3 user input');
  await page.getByPlaceholder('每周可学习时间').fill('3');
  await page.getByPlaceholder('显示模式').fill('professional');
  await page.getByRole('button', { name: '保存档案' }).click();

  await page.getByRole('link', { name: '目标', exact: true }).click();
  await page.getByPlaceholder('目标专业').fill('User phase 3 target');
  await page.getByRole('button', { name: '创建目标' }).click();
  await page.getByRole('link', { name: '差距' }).click();
  await page.getByPlaceholder('要求标题').fill('User verified requirement');
  await page.getByRole('button', { name: '添加已确认要求' }).click();

  await page.getByRole('link', { name: '任务闭环' }).click();
  await page.getByPlaceholder('任务标题').fill('User completed phase 3 task');
  await page.getByPlaceholder('预计时长（分钟）').fill('60');
  await page.getByPlaceholder('完成标准').fill('Submit result and test evidence');
  await page.getByPlaceholder('证据要求').fill('Result and test files');
  await page.getByRole('button', { name: '保存任务' }).click();
  await page.getByRole('button', { name: /User completed phase 3 task/ }).click();

  const file = page.locator('input[type=file]');
  await file.setInputFiles({ name: 'result.txt', mimeType: 'text/plain', buffer: Buffer.from('user result') });
  await page.getByRole('button', { name: '上传证据' }).click();
  await page.getByLabel('成果证据类型').selectOption('test');
  await file.setInputFiles({ name: 'test.txt', mimeType: 'text/plain', buffer: Buffer.from('user test') });
  await page.getByRole('button', { name: '上传证据' }).click();
  await page.getByRole('button', { name: '标记任务完成' }).click();
  await page.getByRole('button', { name: '提交评测' }).click();
  await expect(page.getByText(/评测：completed/)).toBeVisible();
  await page.getByLabel('成果转化类型').selectOption('learning_verified');
  await page.getByLabel('关联能力维度').selectOption('mathematical_foundation');
  await page.getByRole('button', { name: '转化任务成果' }).click();
  await expect(page.getByText('任务成果已转化为背包物品')).toBeVisible();

  await page.getByRole('link', { name: '背包' }).click();
  await expect(page).toHaveURL(/\/inventory/);
  await expect(page.getByText('User completed phase 3 task', { exact: true })).toBeVisible();
  await page.getByRole('link', { name: '变化' }).click();
  await expect(page.getByText('learning_verified')).toBeVisible();

  await page.getByRole('link', { name: '周结算' }).click();
  await page.getByRole('button', { name: '生成本周结算' }).click();
  await expect(page.getByText('结算详情')).toBeVisible();
  await page.getByRole('button', { name: '生成路径调整预览' }).click();
  await page.getByRole('link', { name: '路径调整' }).click();
  await expect(page.getByText(/continue|add_information_task/)).toBeVisible();

  await page.getByRole('link', { name: '下周计划' }).click();
  await page.getByRole('button', { name: '预览下一周计划' }).click();
  await page.getByRole('button', { name: '确认下周计划' }).click();
  await expect(page.getByText('下周计划已写入任务中心。')).toBeVisible();
  await page.getByRole('link', { name: '任务闭环' }).click();
  await expect(page.getByRole('button', { name: /User verified requirement/ })).toBeVisible();
});
