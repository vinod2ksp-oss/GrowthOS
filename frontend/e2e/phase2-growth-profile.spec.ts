import { expect, test } from '@playwright/test';

test('user imports and confirms evidence then creates a seven-day plan', async ({ page }) => {
  const email = `phase2-${Date.now()}@example.com`;
  await page.goto('/register');
  await page.waitForLoadState('networkidle');
  await page.getByPlaceholder('邮箱').fill(email);
  await page.getByPlaceholder('密码').fill('secret123');
  await page.getByRole('button', { name: '注册' }).click();
  await expect(page).toHaveURL(/\/login/);
  await page.getByPlaceholder('邮箱').fill(email);
  await page.getByPlaceholder('密码').fill('secret123');
  await page.getByRole('button', { name: '登录' }).click();
  await page.getByPlaceholder('昵称').fill('Phase 2 user input');
  await page.getByPlaceholder('每周可学习时间').fill('3');
  await page.getByRole('button', { name: '保存档案' }).click();

  await page.getByRole('link', { name: '目标', exact: true }).click();
  await page.getByPlaceholder('目标专业').fill('User entered target');
  await page.getByRole('button', { name: '创建目标' }).click();

  await page.getByRole('link', { name: '材料' }).click();
  await page.getByLabel('选择材料').setInputFiles({ name: 'user-grade.png', mimeType: 'image/png', buffer: Buffer.from('user-owned-image') });
  await page.getByRole('button', { name: '上传材料' }).click();
  await expect(page.getByText('材料已上传，请确认结构化结果')).toBeVisible();
  await page.getByPlaceholder('课程名称').fill('User supplied mathematics course');
  await page.getByPlaceholder('成绩').fill('86');
  await page.getByPlaceholder('满分').fill('100');
  await page.getByRole('button', { name: '确认结构化结果' }).click();
  await expect(page.getByText('解析结果已确认并生成成长证据')).toBeVisible();

  await page.getByRole('link', { name: '证据' }).click();
  await expect(page.getByText('User supplied mathematics course', { exact: true })).toBeVisible();
  await page.getByRole('link', { name: '能力' }).click();
  await expect(page.getByText('86.0% - 86.0%')).toBeVisible();

  await page.getByRole('link', { name: '差距' }).click();
  await page.getByPlaceholder('要求标题').fill('User confirmed mathematics requirement');
  await page.getByPlaceholder('目标最低值（可选）').fill('0.9');
  await page.getByRole('button', { name: '添加已确认要求' }).click();
  await expect(page.getByText('User confirmed mathematics requirement')).toBeVisible();
  await expect(page.getByText(/差距：minor/)).toBeVisible();

  await page.getByRole('link', { name: '七日计划' }).click();
  await page.getByRole('button', { name: '生成七日计划' }).click();
  await expect(page.getByText(/推进 User confirmed mathematics requirement/)).toBeVisible();
  await page.getByRole('button', { name: '确认计划并写入任务中心' }).click();
  await expect(page.getByText('计划已确认，任务已写入任务中心。')).toBeVisible();
  await page.getByRole('link', { name: '任务闭环' }).click();
  await expect(page.getByRole('button', { name: /推进 User confirmed mathematics requirement/ })).toBeVisible();
});
