import { expect, test } from "@playwright/test";

async function registerAndLogin(page: import("@playwright/test").Page, email: string) {
  await page.goto("/register");
  await page.waitForLoadState("networkidle");
  await page.locator("form input").nth(0).fill(email);
  await page.locator("form input").nth(1).fill("secret123");
  await page.locator("form button").click();
  await expect(page).toHaveURL(/\/login/);
  await page.reload();
  await page.waitForLoadState("networkidle");
  await page.locator("form input").nth(0).fill(email);
  await page.locator("form input").nth(1).fill("secret123");
  await page.locator("form button").click();
  await expect(page).toHaveURL(/\/profile/);
}

test("admin resource becomes a rule recommendation with isolated user interactions", async ({ page, request }) => {
  const resourceName = `E2E administrator resource ${Date.now()}`;
  const taskTag = `unique${Date.now()}`;
  const taskTitle = `Practice ${taskTag}`;
  const adminEmail = `phase5-admin-${Date.now()}@example.com`;
  await registerAndLogin(page, adminEmail);
  const promotion = await request.post("http://127.0.0.1:8000/api/v1/test/promote-admin", { data: { email: adminEmail } });
  expect(promotion.ok()).toBeTruthy();
  await page.goto("/admin/resources");
  await page.getByPlaceholder("资源名称").fill(resourceName);
  await page.getByPlaceholder("资源描述").fill("A real test-only resource entered by the administrator");
  await page.getByPlaceholder("提供方").fill("E2E test provider");
  await page.getByPlaceholder("价格").fill("40");
  await page.getByPlaceholder("原始外部链接").fill("https://example.com/resource");
  await page.getByPlaceholder("任务标签，逗号分隔").fill(taskTag);
  await page.getByPlaceholder("目标类型，逗号分隔").fill("preparation");
  await page.getByRole("button", { name: "创建资源草稿" }).click();
  await expect(page.getByText("资源已创建为草稿")).toBeVisible();
  const resourceRow = page.locator("article").filter({ hasText: resourceName });
  await resourceRow.getByRole("button", { name: "上架" }).click();
  await expect(resourceRow.getByText(/active/)).toBeVisible();

  await page.evaluate(() => localStorage.removeItem("growthos_token"));
  const learnerEmail = `phase5-learner-${Date.now()}@example.com`;
  await registerAndLogin(page, learnerEmail);
  const profileInputs = page.locator("form input");
  await profileInputs.nth(0).fill("Phase 5 learner");
  await profileInputs.nth(1).fill("preparation");
  await page.getByPlaceholder("学习资源预算").fill("60");
  await page.locator("form button").click();

  await page.goto("/goals");
  await page.locator("form input").nth(2).fill("User supplied target");
  await page.locator("form input").nth(5).fill("preparation");
  await page.locator("form button").click();
  await page.goto("/goal-analysis");
  await page.getByPlaceholder("要求标题").fill("User mathematics requirement");
  await page.getByPlaceholder("目标最低值（可选）").fill("0.9");
  await page.getByRole("button", { name: "添加已确认要求" }).click();

  await page.goto("/tasks");
  await page.locator("form input").first().fill(taskTitle);
  await page.locator("form button").click();
  await page.goto("/resources");
  const card = page.locator("article").filter({ hasText: resourceName });
  await expect(card.getByText(`关联任务：${taskTitle}`, { exact: true })).toBeVisible();
  await expect(card.getByText("关联能力：mathematical_foundation", { exact: true })).toBeVisible();
  const favoriteRecord = page.waitForResponse((response) => response.url().includes("/favorite") && response.request().method() === "PUT");
  await card.getByRole("button", { name: "收藏" }).click();
  expect((await favoriteRecord).status()).toBe(204);
  await card.getByRole("button", { name: "标记已有" }).click();
  await card.getByRole("link", { name: "查看详情" }).click();
  await expect(page.getByRole("heading", { name: "资源详情" })).toBeVisible();
  await page.getByRole("button", { name: "前往外部资源" }).click();
  await expect(page.getByText("即将前往第三方页面。GrowthOS 不会将此次跳转视为已购买。")).toBeVisible();
  await page.evaluate(() => { window.open = () => null; });
  const clickRecord = page.waitForResponse((response) => response.url().includes("/interactions") && response.request().method() === "POST");
  await page.getByRole("button", { name: "确认前往" }).click();
  expect((await clickRecord).status()).toBe(201);

  await page.goto("/resources/favorites");
  await expect(page.getByText(resourceName)).toBeVisible();
  await page.goto("/resources/owned");
  await expect(page.getByText("商城资源")).toBeVisible();
  await page.goto("/tasks");
  await page.getByRole("button", { name: taskTitle }).click();
  const linkedResource = page.locator("article").filter({ hasText: resourceName });
  await expect(linkedResource).toBeVisible();
  await linkedResource.getByRole("button", { name: "用于此任务" }).click();
  await expect(page.getByText("已记录该资源用于当前任务；任务状态和能力值未改变。")).toBeVisible();
});
