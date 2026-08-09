import { expect, test } from "@playwright/test";

test("optional AI layer preserves confirmation and rule-controlled workflow", async ({ page }) => {
  const email = `phase4-${Date.now()}@example.com`;
  await page.goto("/register");
  const registerInputs = page.locator("form input");
  await registerInputs.nth(0).fill(email);
  await registerInputs.nth(1).fill("secret123");
  await page.locator("form button").click();
  await expect(page).toHaveURL(/\/login/);
  const loginInputs = page.locator("form input");
  await loginInputs.nth(0).fill(email);
  await loginInputs.nth(1).fill("secret123");
  await page.locator("form button").click();
  await expect(page).toHaveURL(/\/profile/);

  const profileInputs = page.locator("form input");
  await profileInputs.nth(0).fill("Phase 4 user");
  await profileInputs.nth(6).fill("3");
  await page.locator("form button").click();

  await page.goto("/ai-settings");
  await expect(page.getByText("当前状态：可用")).toBeVisible();
  await page.getByRole("checkbox").check();

  await page.goto("/goals");
  await page.locator("form input").nth(2).fill("User supplied phase 4 target");
  await page.locator("form button").click();

  await page.goto("/materials");
  await page.getByLabel("选择材料").setInputFiles({ name: "user-transcript.txt", mimeType: "text/plain", buffer: Buffer.from("User course score 84 out of 100") });
  await page.getByRole("button", { name: "上传材料" }).click();
  await page.getByRole("button", { name: "AI 辅助解析" }).click();
  await expect(page.getByText("AI 草稿已回填，请核对后再确认。" )).toBeVisible();
  await page.getByRole("button", { name: "确认 AI 草稿并生成证据" }).click();
  await expect(page.getByText("AI 草稿已由你确认并生成成长证据")).toBeVisible();

  await page.goto("/attributes");
  const mathCard = page.locator("article").filter({ hasText: "mathematical_foundation" });
  await expect(mathCard.getByText("84.0% - 84.0%")).toBeVisible();
  await mathCard.getByRole("button", { name: "AI 解读" }).click();
  await expect(mathCard.getByText("The rule diagnosis is supported by confirmed user evidence.")).toBeVisible();

  await page.goto("/goal-analysis");
  await page.getByLabel("用户提供的目标要求文本").fill("User supplied mathematics ratio requirement 90 percent");
  await page.getByRole("button", { name: "AI 整理要求" }).click();
  await expect(page.getByText("E2E supplied requirement")).toBeVisible();
  await page.getByRole("button", { name: "确认 AI 整理结果" }).click();
  await expect(page.getByText("AI 草稿已由你确认并写入目标要求")).toBeVisible();

  await page.goto("/weekly-plan");
  await page.getByRole("button", { name: "生成七日计划" }).click();
  await page.getByRole("button", { name: "AI 优化任务" }).click();
  await expect(page.getByText(/AI refined/).first()).toBeVisible();
  await page.getByRole("button", { name: "应用 AI 优化草稿" }).click();
  await page.getByRole("button", { name: "确认计划并写入任务中心" }).click();
  await expect(page.getByText("计划已确认，任务已写入任务中心。" )).toBeVisible();

  await page.goto("/tasks");
  const taskButton = page.getByRole("button", { name: /AI refined/ }).first();
  await expect(taskButton).toBeVisible();
  await taskButton.click();
  const detail = page.locator("main > section").last();
  const evidenceFile = detail.locator('input[type="file"]');
  await evidenceFile.setInputFiles({ name: "result.txt", mimeType: "text/plain", buffer: Buffer.from("user result") });
  await detail.getByRole("button", { name: /上传证据/ }).click();
  await detail.locator("select").first().selectOption("test");
  await evidenceFile.setInputFiles({ name: "test.txt", mimeType: "text/plain", buffer: Buffer.from("user test") });
  await detail.getByRole("button", { name: /上传证据/ }).click();
  await detail.getByRole("button", { name: /标记任务完成/ }).click();
  await detail.getByRole("button", { name: /提交评测/ }).click();
  await detail.getByRole("button", { name: "AI 深度反馈" }).click();
  await expect(detail.getByText("Feedback grounded in the rule evaluation.")).toBeVisible();
});
