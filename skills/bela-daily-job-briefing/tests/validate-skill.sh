#!/bin/bash
# daily-job-briefing skill 结构与逻辑一致性验证
# 用法: bash tests/validate-skill.sh

cd "$(dirname "$0")/.." || exit 1
PASS=0
FAIL=0
WARN=0

pass() { echo "  ✅ $1"; ((PASS++)); }
fail() { echo "  ❌ $1"; ((FAIL++)); }
warn() { echo "  ⚠️  $1"; ((WARN++)); }

echo "=== 1. 文件结构检查 ==="

# SKILL.md 引用的所有文件必须存在
for f in \
  "templates/user-profile-template.md" \
  "templates/daily-job-report.md" \
  "templates/bookmarks-template.md" \
  "references/search-sources.md" \
  "shared/.gitkeep" \
  ".gitignore" \
  "LICENSE.txt" \
  "README.md"; do
  [ -f "$f" ] && pass "$f 存在" || fail "$f 缺失"
done

# shared/ 目录存在
[ -d "shared" ] && pass "shared/ 目录存在" || fail "shared/ 目录不存在（git clone 后会丢失）"

echo ""
echo "=== 2. SKILL.md 内部引用一致性 ==="

SKILL="SKILL.md"

# 支撑文件索引中的每个文件路径在 SKILL.md 其他位置也有引用
for ref in "shared/user-profile.md" "shared/bookmarks.md" "shared/resume/" "shared/reports/" "shared/report-index.md" "templates/daily-job-report.md" "templates/bookmarks-template.md" "references/search-sources.md"; do
  count=$(grep -c "$ref" "$SKILL")
  [ "$count" -ge 2 ] && pass "$ref 在 SKILL.md 中引用 ${count} 次（索引+正文）" || warn "$ref 仅在索引中出现，正文未引用"
done

echo ""
echo "=== 3. 符号一致性检查 ==="

# 薪资可信度应该用 ✅/⚠️/❓，不应该用 🟢/🟡/🔴
if grep -q "薪资.*🟢\|薪资.*🟡\|薪资.*🔴" "$SKILL"; then
  fail "SKILL.md 薪资可信度仍使用旧符号 🟢/🟡/🔴（应为 ✅/⚠️/❓）"
else
  pass "SKILL.md 薪资可信度符号正确（✅/⚠️/❓）"
fi

# 日报模板中薪资符号也要一致
TPL="templates/daily-job-report.md"
if grep -q "薪资.*🟢\|预估薪资.*🟢" "$TPL"; then
  fail "日报模板薪资可信度仍使用旧符号"
else
  pass "日报模板薪资可信度符号正确"
fi

# 岗位状态应该用 🟢/🟡
if grep -q "岗位状态.*🟢\|状态.*🟢.*确认\|状态.*🟡.*待确认" "$TPL"; then
  pass "日报模板岗位状态符号正确（🟢/🟡）"
else
  warn "日报模板中未找到岗位状态符号说明"
fi

echo ""
echo "=== 4. Onboarding 问题完整性 ==="

for q in 1 2 3 4 5 6 7 8; do
  if grep -qE "^${q}\." "$SKILL"; then
    pass "Q${q} 存在"
  else
    fail "Q${q} 缺失"
  fi
done

# Q5 应包含"构成"相关内容
if grep -A3 "^5\." "$SKILL" | grep -qi "构成\|期权\|现金"; then
  pass "Q5 包含薪资构成偏好"
else
  fail "Q5 缺少薪资构成偏好"
fi

# Q7 应包含公司偏好选项
if grep -A8 "^7\." "$SKILL" | grep -qi "大厂\|创业\|外企\|国企"; then
  pass "Q7 包含公司偏好选项"
else
  fail "Q7 缺少公司偏好选项"
fi

# Q8 应包含排除条件
if grep -A3 "^8\." "$SKILL" | grep -qi "不考虑\|排除\|前东家"; then
  pass "Q8 包含排除条件"
else
  fail "Q8 缺少排除条件"
fi

echo ""
echo "=== 5. 模式覆盖检查 ==="

for mode in "A 完整日报\|A.*完整" "B 快速日报\|B.*快速" "C 定向追踪\|C.*定向" "D 回看\|D.*回看" "E 标记追踪\|E.*标记" "F 市场概览\|F.*市场"; do
  if grep -qE "$mode" "$SKILL"; then
    label=$(echo "$mode" | sed 's/\\|.*//;s/\.\*//')
    pass "Mode $label 已定义"
  else
    fail "Mode 缺失: $mode"
  fi
done

# Mode B 应包含 Step 5
if grep -A1 "B.*快速" "$SKILL" | grep -q "Step 5"; then
  pass "Mode B 包含 Step 5（保存）"
else
  fail "Mode B 未包含 Step 5"
fi

# Mode D 应有无历史日报的兜底
if grep -A1 "D.*回看" "$SKILL" | grep -qi "无.*日报\|不存在\|先生成"; then
  pass "Mode D 有无历史日报兜底"
else
  fail "Mode D 缺少无历史日报兜底"
fi

echo ""
echo "=== 6. 质量标准检查 ==="

# 七要素
if grep -q "七要素" "$SKILL"; then
  pass "质量标准引用'七要素'（非六要素）"
else
  fail "质量标准仍引用'六要素'或未提及"
fi

# 搜索总量上限
if grep -q "15 次\|≤ 15" "$SKILL"; then
  pass "搜索总量上限已设定"
else
  fail "未设定搜索总量上限"
fi

# URL 幻觉防护
if grep -qi "严禁编造.*URL\|禁止编造" "$SKILL"; then
  pass "URL 幻觉防护规则存在"
else
  fail "缺少 URL 幻觉防护规则"
fi

# Mode B 质量清单豁免
if grep -q "Mode B.*豁免\|Mode B 豁免" "$SKILL"; then
  pass "Mode B 市场行情豁免标注存在"
else
  fail "Mode B 市场行情豁免标注缺失"
fi

echo ""
echo "=== 7. .gitignore 检查 ==="

GI=".gitignore"
if grep -q "shared/\*" "$GI" || grep -q "shared/" "$GI"; then
  pass ".gitignore 排除 shared/ 运行时数据"
else
  fail ".gitignore 未排除 shared/"
fi

if grep -q "\.gitkeep" "$GI"; then
  pass ".gitignore 保留 .gitkeep"
else
  fail ".gitignore 未保留 .gitkeep"
fi

# README.md 不应被 gitignore
if grep -q "README.md" "$GI"; then
  fail ".gitignore 排除了 README.md（不应排除）"
else
  pass "README.md 未被 gitignore"
fi

echo ""
echo "=== 8. README 检查 ==="

README="README.md"
if grep -qi "隐私\|数据\|privacy" "$README"; then
  pass "README 包含隐私/数据说明"
else
  fail "README 缺少隐私/数据说明"
fi

if grep -q "report-index\|reports/" "$README"; then
  pass "README 目录结构包含 reports"
else
  fail "README 目录结构未更新"
fi

echo ""
echo "=== 9. 跨文件一致性 ==="

# search-sources.md 应有维护提示
if grep -qi "维护提示\|URL.*失效\|定期" "references/search-sources.md"; then
  pass "search-sources.md 包含维护提示"
else
  fail "search-sources.md 缺少维护提示"
fi

# user-profile-template 应有薪资构成字段
if grep -qi "构成\|现金.*期权\|薪资构成" "templates/user-profile-template.md"; then
  pass "user-profile-template 包含薪资构成偏好字段"
else
  warn "user-profile-template 缺少薪资构成偏好字段（Q5 扩展后应同步）"
fi

# user-profile-template 应有公司偏好字段
if grep -qi "公司偏好\|公司类型\|目标公司" "templates/user-profile-template.md"; then
  pass "user-profile-template 包含公司相关字段"
else
  warn "user-profile-template 缺少公司偏好字段（Q7 新增后应同步）"
fi

# user-profile-template 应有排除条件字段
if grep -qi "排除\|不考虑\|黑名单" "templates/user-profile-template.md"; then
  pass "user-profile-template 包含排除条件字段"
else
  warn "user-profile-template 缺少排除条件字段（Q8 新增后应同步）"
fi

echo ""
echo "==========================================="
echo "  结果: ✅ $PASS 通过  ❌ $FAIL 失败  ⚠️  $WARN 警告"
echo "==========================================="

[ "$FAIL" -eq 0 ] && exit 0 || exit 1
