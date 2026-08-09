import { expect, test } from '@playwright/test';

test('user completes the GrowthOS phase-one loop from pages', async ({ page }) => {
  const email = `ui-${Date.now()}@example.com`;
  await page.goto('/register');
  await page.waitForLoadState('networkidle');
  await page.getByPlaceholder('邮箱').fill(email);
  await page.getByPlaceholder('密码').fill('secret123');
  await page.getByRole('button', { name: '注册' }).click();
  await expect(page).toHaveURL(/\/login/);
  await page.getByPlaceholder('邮箱').fill(email);
  await page.getByPlaceholder('密码').fill('secret123');
  await page.getByRole('button', { name: '登录' }).click();
  await expect(page).toHaveURL(/\/profile/);
  await page.getByPlaceholder('昵称').fill('UI verification');
  await page.getByRole('button', { name: '保存档案' }).click();
  await expect(page.getByText('档案已保存')).toBeVisible();

  await page.getByRole('link', { name: '目标' }).click();
  await page.getByPlaceholder('目标专业').fill('Software Engineering');
  await page.getByRole('button', { name: '创建目标' }).click();
  await expect(page.getByText('目标已创建')).toBeVisible();

  await page.getByRole('link', { name: '任务闭环' }).click();
  await page.getByPlaceholder('任务标题').fill('Main UI task');
  await page.getByRole('button', { name: '保存任务' }).click();
  await page.getByPlaceholder('任务标题').fill('Sub UI task');
  await page.locator('select').nth(1).selectOption('subtask');
  await page.getByLabel('父任务').selectOption({ label: 'Main UI task' });
  await page.getByRole('button', { name: '保存任务' }).click();
  await page.getByRole('button', { name: /Main UI task/ }).click();
  await page.getByRole('button', { name: '开始计时' }).click();
  await page.getByRole('button', { name: '暂停' }).click();
  await page.getByRole('button', { name: '恢复' }).click();
  await page.getByRole('button', { name: '结束' }).click();
  await page.locator('input[type=file]').setInputFiles({ name: 'result.txt', mimeType: 'text/plain', buffer: Buffer.from('verified') });
  await page.getByRole('button', { name: '上传证据' }).click();
  await expect(page.getByText('证据已上传')).toBeVisible();
  await page.getByRole('button', { name: '提交评测' }).click();
  await expect(page.getByText(/评测：/)).toBeVisible();
  await page.getByRole('button', { name: '查询结果' }).click();
  await expect(page.getByText(/评测：/)).toBeVisible();
});
