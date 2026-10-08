#!/usr/bin/env python3
"""Plugin packaging, generation and eval-contract integration tests."""
import json
import os
import re
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
SCRIPTS = ROOT / "scripts"
sys.path.insert(0, str(SCRIPTS))
from budget import calculate_position_overview, format_position_overview  # noqa: E402
from decision_model import validate_decision  # noqa: E402
from user_state import load_state, save_state  # noqa: E402

SKILLS = {"swt", "swt-application", "swt-position", "swt-english", "swt-visa", "swt-arrival"}
INTENTS = {"NAVIGATION", "DOCUMENT_CHECK", "DECISION", "ENGLISH_ASSESSMENT", "ENGLISH_PRACTICE", "ENGLISH_MOCK", "ENGLISH_RECORDING", "ENGLISH_RETRY", "ENGLISH_PROGRESS", "GENERAL_ENGLISH", "FORM_FILLING", "CONFLICT", "CALCULATION", "EMERGENCY", "GENERAL_QA"}

class PackageTests(unittest.TestCase):
    def test_manifests_agree(self):
        portable = json.loads((ROOT / "plugin.json").read_text(encoding="utf-8"))
        compat = json.loads((ROOT / ".codex-plugin/plugin.json").read_text(encoding="utf-8"))
        for key in ("name", "version", "description", "author"):
            if key == "version":
                self.assertEqual(portable[key].split("+", 1)[0], compat[key].split("+", 1)[0])
            else:
                self.assertEqual(portable[key], compat[key])
        self.assertEqual(portable["name"], "howto-swt")
        self.assertEqual(portable["version"], "1.2.0")
        self.assertEqual(compat["skills"], "./skills/")
        self.assertEqual(compat["author"]["name"], "Howard")
        self.assertEqual(compat["interface"]["displayName"], "HowTo SWT")
        readme = (ROOT / "README.md").read_text(encoding="utf-8")
        changelog = (ROOT / "docs/CHANGELOG.md").read_text(encoding="utf-8")
        eval_spec = json.loads((ROOT / "tests/evals/cases/evals.json").read_text(encoding="utf-8"))
        self.assertIn("# HowTo SWT", readme)
        self.assertIn("v1.2.0", readme)
        self.assertIn("## v1.0.0 — howto-swt.skill Production Architecture", changelog)
        self.assertIn("## v0.9.0 — Structured Decision Architecture", changelog)
        self.assertEqual(eval_spec["product"], "HowTo SWT")
        self.assertEqual(eval_spec["plugin"], "howto-swt")
        self.assertEqual(eval_spec["version"], "1.2.0")
        install = (ROOT / "docs/INSTALL.md").read_text(encoding="utf-8")
        self.assertIn("0x-howard/howto-swt", install)
        self.assertNotIn("远端仓库改名和发布完成前", readme)

    def test_exactly_six_discoverable_skills(self):
        found = {p.parent.name for p in (ROOT / "skills").glob("*/SKILL.md")}
        self.assertEqual(found, SKILLS)
        for skill in SKILLS:
            content = (ROOT / "skills" / skill / "SKILL.md").read_text(encoding="utf-8")
            match = re.match(r"^---\n(.*?)\n---\n", content, re.DOTALL)
            self.assertIsNotNone(match)
            frontmatter = match.group(1)
            self.assertRegex(frontmatter, rf"(?m)^name:\s*{re.escape(skill)}$")
            self.assertRegex(frontmatter, r"(?m)^description:\s*\S+")
            if skill == "swt":
                description = re.search(r"(?m)^description:\s*(.+)$", frontmatter).group(1)
                self.assertLessEqual(len(description), 1024)
                for alias in ("小How", "小how", "小 HOW", "HowToSWT", "howtoswt", "HowTo SWT", "howto swt", "howto-swt"):
                    self.assertIn(alias, description)
                for ordinary_greeting in ("你好", "hello", "hi", "在吗"):
                    self.assertIn(ordinary_greeting, description)

    def test_shared_runtime_is_current(self):
        result = subprocess.run(
            [sys.executable, str(SCRIPTS / "sync_shared.py"), "--check"],
            cwd=ROOT,
            text=True,
            capture_output=True,
            check=False,
        )
        self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
        for skill in SKILLS:
            self.assertTrue((ROOT / "references/shared-runtime" / f"{skill}.md").is_file())

    def test_shared_single_source_and_attribution_injection(self):
        source = (ROOT / "shared/creator-attribution.md").read_text(encoding="utf-8")
        marker = "HowTo SWT\n作者：Howard\n@哎哟不想上早八啊（全平台同名）"
        self.assertEqual(source.count(marker), 1)
        for skill in SKILLS:
            runtime = (ROOT / "references/shared-runtime" / f"{skill}.md").read_text(encoding="utf-8")
            self.assertEqual(runtime.count(marker), 1)
            self.assertIn("GENERATED FILE: DO NOT EDIT", runtime)
            self.assertIn("runtime-version: 1.2.0", runtime)
            self.assertIn("Structured Decision Architecture", runtime)
            self.assertIn("USER_DATA_ROOT", runtime)
            self.assertIn("source: shared/editorial-policy.md", runtime)

    def test_persona_and_creator_attribution_are_independent(self):
        identity = (ROOT / "shared/creator-attribution.md").read_text(encoding="utf-8")
        homepage = (ROOT / "skills/swt/SKILL.md").read_text(encoding="utf-8")
        marker = "想让小How持续记住你的 SWT 进度并获得真人陪跑？加入 HowTo SWT Pro。\n作者：Howard｜@哎哟不想上早八啊（全平台同名）"
        self.assertIn("小How", identity)
        self.assertIn("你好，我在。你可以直接选一项：", homepage)
        self.assertNotIn("欢迎使用 HowTo SWT，我是你的 SWT 助手小How。", homepage)
        self.assertIn("仅在 HowTo SWT 已激活", homepage)
        self.assertIn("用户只说“你好”“hello”“hi”或“在吗”时，不要求未激活的宿主抢占", homepage)
        self.assertIn("HowTo SWT 怎么用", homepage)
        self.assertIn("HowTo SWT\n作者：Howard", identity)
        footer = re.sub(r"  \n", "\n", homepage)
        self.assertIn(marker, footer)
        self.assertEqual(footer.count(marker), 1)
        self.assertIn("不展示首页，立即处理任务", identity)
        self.assertIn("同一 conversation 后续不重复自我介绍", identity)
        self.assertEqual(identity.count("HowTo SWT\n作者：Howard"), 1)

    def test_router_is_two_stage_and_free_ad_stays_outside_handoff(self):
        router = (ROOT / "skills/swt/SKILL.md").read_text(encoding="utf-8")
        handoff = (ROOT / "shared/handoff-contract.md").read_text(encoding="utf-8")
        for item in (
            "1. 报名 / 申请", "2. 岗位 / Offer", "3. 英语测评 / 面试练习",
            "4. Visa", "5. 行前 / 入境 / 美国生活", "6. 不确定，帮我判断下一步",
        ):
            self.assertIn(item, router)
        self.assertIn("生成 Prompt 后无条件 STOP", router)
        self.assertIn("Router → Handoff Prompt → STOP", handoff)
        self.assertIn("HOWTO_SWT_HANDOFF_V1", handoff)
        self.assertNotIn("加入 HowTo SWT Pro", handoff)
        start = router.index("<!-- FREE_ROUTER_AD_START -->")
        end = router.index("<!-- FREE_ROUTER_AD_END -->")
        ad = router[start:end]
        self.assertEqual(ad.count("加入 HowTo SWT Pro"), 1)

    def test_current_naming_and_discovery_metadata(self):
        names = ("swt", "swt-application", "swt-position", "swt-english", "swt-visa", "swt-arrival")
        self.assertEqual({p.parent.name for p in (ROOT / "skills").glob("*/SKILL.md")}, set(names))

        readme = (ROOT / "README.md").read_text(encoding="utf-8")
        source = (ROOT / "shared/creator-attribution.md").read_text(encoding="utf-8")
        homepage = (ROOT / "skills/swt/SKILL.md").read_text(encoding="utf-8")
        manifest = json.loads((ROOT / ".codex-plugin/plugin.json").read_text(encoding="utf-8"))
        current_docs = (readme, source, homepage, manifest["description"], manifest["interface"]["displayName"])
        for old_name in ("swt-skill", "swt-plugin", "howto-swt.skill"):
            self.assertTrue(all(old_name not in content for content in current_docs), old_name)
        self.assertIn("J-1 Summer Work Travel", readme)
        self.assertIn("SWT English", readme)
        self.assertIn("## 03 Free vs Pro", readme)
        self.assertIn("## 02 Agent 安装", readme)
        self.assertIn("swt-plugin", (ROOT / "docs/CHANGELOG.md").read_text(encoding="utf-8"))

    def test_structured_compression_architecture_and_fixture(self):
        framework = (ROOT / "shared/answer-framework.md").read_text(encoding="utf-8")
        policy = (ROOT / "shared/editorial-policy.md").read_text(encoding="utf-8")
        for stage in ("Analyze", "Compress", "Present", "Edit"):
            self.assertIn(stage, framework)
        for priority in ("P1", "P2", "P3", "P4"):
            self.assertIn(priority, framework)
        self.assertIn("RAW INFORMATION ≠ USER ANSWER", framework)
        self.assertIn("Clarity Gate", policy)
        self.assertIn("若否，重新组织回答", policy)

        fixture = ROOT / "tests/evals/fixtures"
        after = (ROOT / "tests/evals/expected/position_compare_ssn_dependency_expected.md").read_text(encoding="utf-8")
        input_data = json.loads((fixture / "position_compare_ssn_dependency_input.json").read_text(encoding="utf-8"))
        self.assertEqual(after.strip(), format_position_overview(calculate_position_overview(input_data)).strip())
        self.assertEqual(re.findall(r"(?m)^## \d\. [^\n]+", after), [
            "## 1. 核心数据", "## 2. 回本测算", "## 3. 岗位收益函数 / ROI Comparison", "## 4. 注意事项", "## 5. 继续看什么？",
        ])
        self.assertEqual(len(re.findall(r"(?m)^\|---(?:\|---)+\|$", after)), 4)
        self.assertIn("Hotel B（City B）的预计缺口最小", after.splitlines()[0])
        self.assertIn("最终预计结余", after)
        self.assertIn("预计税费", after)
        self.assertIn("¥20,000", after)
        self.assertIn("延迟到账不等于工资损失", after)
        self.assertIn("Restaurant A", after)
        self.assertIn("Hotel B", after)

    def test_detail_cli_does_not_reprint_overview(self):
        result = subprocess.run(
            [sys.executable, str(SCRIPTS / "budget.py"), "--detail", "housing", str(ROOT / "assets/position-overview-example.json")],
            cwd=ROOT, text=True, capture_output=True, check=False,
        )
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertIn("住宿按", result.stdout)
        self.assertNotIn("## 1.", result.stdout)

    def test_router_contract(self):
        router = (ROOT / "shared/routing-policy.md").read_text(encoding="utf-8")
        for intent in INTENTS:
            self.assertIn(intent, router)
        for dimension in ("Task Type", "SWT Stage", "Known Context", "Risk Level"):
            self.assertIn(dimension, router)
        for skill in SKILLS:
            self.assertIn(f"`{skill}`", router + (ROOT / "skills/swt/SKILL.md").read_text(encoding="utf-8"))

    def test_canonical_references_are_bundled_from_root_sources(self):
        expected = {
            "swt-application": {"agency-sponsor.md", "application-materials.md"},
            "swt-position": {"location-offer.md", "budget-method.md", "tax-estimation.md", "state-income-tax.md", "default-assumptions.json"},
            "swt-english": {
                "english-practice.md", "english-assessment.md", "english-rubric.md",
                "english-profiles.md", "english-question-bank.md", "english-speaking-coach.md",
            },
            "swt-visa": {"visa-ds2019.md"},
            "swt-arrival": {"predeparture-program.md"},
            "swt": set(),
        }
        for skill, references in expected.items():
            root = ROOT / "skills" / skill
            content = (root / "SKILL.md").read_text(encoding="utf-8")
            self.assertLessEqual({path.name for path in root.iterdir()}, {"SKILL.md", "references", "scripts", "assets"})
            self.assertIn(f"references/shared-runtime/{skill}.md", content)
            self.assertNotIn("../../references/", content)
            self.assertTrue((root / "references/shared-runtime" / f"{skill}.md").is_file())
            self.assertTrue((root / "references/user-state.schema.json").is_file())
            for name in references:
                self.assertTrue((ROOT / "references" / name).is_file())
                self.assertTrue((root / "references" / name).is_file())
                self.assertIn(f"references/{name}", content)
            for path in (root / "references").rglob("*.md"):
                for target in re.findall(r"\[[^\]]*\]\(([^)]+)\)", path.read_text(encoding="utf-8")):
                    target = target.strip("<>")
                    if target.startswith(("http://", "https://", "#", "mailto:")):
                        continue
                    relative = target.split("#", 1)[0]
                    if relative:
                        self.assertTrue((path.parent / relative).resolve().exists(), f"{path}: {target}")

    def test_flat_runtime_mapping_rewrites_only_deployment_copy(self):
        with tempfile.TemporaryDirectory() as directory:
            result = subprocess.run(
                [sys.executable, str(SCRIPTS / "sync_shared.py"), "--runtime-root", directory],
                cwd=ROOT,
                text=True,
                capture_output=True,
                check=False,
            )
            self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
            installed = Path(directory) / "swt-position"
            position = (installed / "SKILL.md").read_text(encoding="utf-8")
            self.assertIn("references/shared-runtime/swt-position.md", position)
            self.assertNotIn("../../references/", position)
            self.assertTrue((installed / "references/knowledge/state_context/STATE_INDEX.md").is_file())
            self.assertTrue((installed / "references/user-state.schema.json").is_file())
            self.assertTrue((installed / "scripts/decision_model.py").is_file())
            self.assertTrue((installed / "scripts/user_state.py").is_file())
            self.assertTrue((installed / "references/budget-method.md").is_file())
            self.assertTrue((installed / "references/default-assumptions.json").is_file())
            self.assertTrue((installed / "scripts/state_context.py").is_file())
            self.assertFalse((installed / "scripts/sync_shared.py").exists())
            self.assertTrue((installed / "assets/net-income-example.json").is_file())
            route = subprocess.run(
                [sys.executable, str(installed / "scripts/state_context.py"), "resolve", "Myrtle Beach"],
                cwd=installed,
                text=True,
                capture_output=True,
                check=False,
            )
            self.assertEqual(route.returncode, 0, route.stdout + route.stderr)
            self.assertIn('"state": "SC"', route.stdout)
            overview = subprocess.run(
                [sys.executable, str(installed / "scripts/budget.py"), str(installed / "assets/position-overview-example.json")],
                cwd=installed, text=True, capture_output=True, check=False,
            )
            self.assertEqual(overview.returncode, 0, overview.stdout + overview.stderr)
            self.assertIn("## 2. 回本测算", overview.stdout)
            english = Path(directory) / "swt-english"
            self.assertTrue((english / "scripts/speaking_score.py").is_file())
            self.assertTrue((english / "references/english-practice.md").is_file())
            for reference in ("english-rubric.md", "english-profiles.md", "english-question-bank.md", "english-assessment.md"):
                self.assertTrue((english / "references" / reference).is_file())
            sample = Path(directory) / "assessment-input.json"
            sample.write_text('{"input_mode":"text","criteria":{}}', encoding="utf-8")
            score = subprocess.run(
                [sys.executable, str(english / "scripts/speaking_score.py"), "--profile", "sponsor_generic", "--input", str(sample)],
                cwd=english, text=True, capture_output=True, check=False,
            )
            self.assertEqual(score.returncode, 0, score.stderr)
            self.assertIn('"readiness_status": "partial"', score.stdout)
            self.assertIn('"audio_required"', score.stdout)

    def test_no_duplicate_state_or_shared_scripts_in_source(self):
        self.assertEqual(len(list((ROOT / "references/knowledge/state_context").glob("STATE_INDEX.md"))), 1)
        self.assertEqual(len(list(ROOT.rglob("state_context.py"))), 2)
        self.assertEqual(len(list(ROOT.rglob("budget.py"))), 2)
        self.assertEqual(len(list((ROOT / "skills").glob("*/references/shared-runtime/*.md"))), 6)
        self.assertTrue((ROOT / "references/english-practice.md").is_file())

    def test_local_markdown_links_resolve(self):
        pattern = re.compile(r"\[[^\]]*\]\(([^)]+)\)")
        for path in ROOT.rglob("*.md"):
            for target in pattern.findall(path.read_text(encoding="utf-8")):
                target = target.strip("<>")
                if target.startswith(("http://", "https://", "#", "mailto:")):
                    continue
                target = target.split("#", 1)[0]
                self.assertTrue((path.parent / target).resolve().exists(), f"{path}: {target}")

    def test_readme_is_a_user_homepage_with_valid_anchors(self):
        readme = (ROOT / "README.md").read_text(encoding="utf-8")
        install = (ROOT / "docs/INSTALL.md").read_text(encoding="utf-8")
        self.assertIn("# HowTo SWT", readme)
        self.assertIn("## 01 Hero", readme)
        self.assertIn("## 02 Agent 安装", readme)
        self.assertIn("## 03 Free vs Pro", readme)
        self.assertIn("## 04 核心能力", readme)
        self.assertIn("## 05 使用方式", readme)
        self.assertIn("npx -y skills add 0x-howard/howto-swt -g --all", install)
        self.assertNotIn("远端仓库改名和发布完成前", readme)
        self.assertIn("## 06 数据与隐私", readme)
        self.assertIn("docs/INSTALL.md", readme)
        self.assertIn("## 07 最近 5 个版本", readme)
        self.assertIn("## 08 Author", readme)
        self.assertNotIn("personal", readme.lower())
        self.assertNotIn("codex plugin add", readme.lower())
        self.assertIn("WorkBuddy", readme)
        recent_versions = re.findall(r"(?m)^\| v\d+\.\d+\.\d+ \|", readme)
        self.assertEqual(len(recent_versions), 5)

        def github_slug(heading):
            slug = heading.strip().lower()
            slug = re.sub(r"[^\w\- ]", "", slug, flags=re.UNICODE)
            return re.sub(r"\s+", "-", slug).strip("-")

        headings = {
            github_slug(match.group(1))
            for match in re.finditer(r"(?m)^#{1,6}\s+(.+?)\s*#*\s*$", readme)
        }
        anchors = re.findall(r"\[[^\]]+\]\(#([^)]+)\)", readme)
        for anchor in anchors:
            self.assertIn(anchor, headings, f"README anchor has no heading: #{anchor}")

    def test_behavior_contract_has_all_required_cases(self):
        data = json.loads((ROOT / "tests/evals/cases/evals.json").read_text(encoding="utf-8"))
        self.assertGreaterEqual(len(data["cases"]), 24)
        self.assertEqual(len(data["reader_facing_rubric"]), 5)
        ids = {case["id"] for case in data["cases"]}
        self.assertEqual(len(ids), len(data["cases"]))
        for case_id in (
            "activation-01-brand-greeting",
            "activation-02-main-brand-name",
            "activation-03-lowercase-brand-alias",
            "activation-04-hyphenated-brand-alias",
            "activation-05-direct-position-task",
            "activation-06-direct-english-task",
            "activation-07-ordinary-greeting-no-trigger",
            "activation-08-active-greeting-homepage",
            "activation-09-bare-persona-name",
            "activation-10-workbuddy-greeting-no-trigger",
            "calculation-12-direct-net-income", "calculation-13-choice-first-missing-fields",
            "calculation-14-date-week-conflict", "calculation-15-tax-modes",
            "calculation-16-state-assisted-pending", "calculation-17-multiple-offers-and-fx",
            "state-context-18-myrtle-beach", "state-context-19-wisconsin-dells",
            "state-context-20-ocean-city", "state-context-21-explicit-state",
            "state-context-22-offer-priority", "state-context-23-unknown-location",
            "state-context-24-schema-and-wording",
            "position-27-ssn-dependency-overview",
            "compression-28-navigation", "compression-29-visa-conflict",
            "compression-30-application-status", "compression-31-english-feedback",
            "position-overview-32-minimum-input", "position-overview-33-rent-override",
            "position-overview-34-state-over-global", "position-overview-35-two-offers-three-tables",
            "position-overview-36-caution-dash", "position-overview-37-housing-followup",
            "position-overview-38-hours-recalculation", "position-overview-39-food-override",
        ):
            self.assertIn(case_id, ids)
        for number in range(1, 21):
            self.assertEqual(
                sum(case_id.startswith(f"english-assessment-{number:02d}-") for case_id in ids), 1
            )
            self.assertEqual(
                sum(case_id.startswith(f"english-practice-{number:02d}-") for case_id in ids), 1
            )
        fixture_paths = (
            ROOT / "tests/evals/fixtures/position_compare_ssn_dependency_input.json",
            ROOT / "tests/evals/expected/position_compare_ssn_dependency_expected.md",
            ROOT / "tests/evals/cases/position_compare_ssn_dependency.md",
        )
        self.assertTrue(all(path.is_file() for path in fixture_paths))
        self.assertEqual(len(json.loads((ROOT / "tests/evals/cases/evals.json").read_text(encoding="utf-8"))["cases"]), len(ids))

    def test_net_income_calculator_is_packaged(self):
        self.assertTrue((SCRIPTS / "budget.py").is_file())
        self.assertTrue((ROOT / "assets/net-income-example.json").is_file())
        self.assertTrue((ROOT / "assets/position-overview-example.json").is_file())
        position = (ROOT / "skills/swt-position/SKILL.md").read_text(encoding="utf-8")
        self.assertIn("position_overview", position)
        self.assertIn("scripts/budget.py", position)

    def test_english_assessment_files_are_packaged(self):
        english = (ROOT / "skills/swt-english/SKILL.md").read_text(encoding="utf-8")
        for reference in (
            "english-assessment.md", "english-rubric.md", "english-profiles.md",
            "english-question-bank.md", "scripts/speaking_score.py",
        ):
            self.assertIn(reference, english)
        for reference in (
            "english-assessment.md", "english-rubric.md", "english-profiles.md",
            "english-question-bank.md",
        ):
            self.assertTrue((ROOT / "references" / reference).is_file())

    def test_english_practice_contract_is_packaged_without_new_skill(self):
        skill = (ROOT / "skills/swt-english/SKILL.md").read_text(encoding="utf-8")
        practice = (ROOT / "references/english-practice.md").read_text(encoding="utf-8")
        state = (ROOT / "shared/state-schema.md").read_text(encoding="utf-8")
        for token in ("agency_practice", "sponsor_practice", "host_practice", "visa_interview_practice"):
            self.assertIn(token, practice)
        for token in ("full_mock", "weakness_drill", "follow_up_drill", "question_drill", "scenario_drill"):
            self.assertIn(token, practice)
        self.assertIn("english_practice:", state)
        self.assertIn("Practice 即时表现", practice)
        self.assertIn("`improved_dimensions`", practice)
        self.assertIn("正式进入 `ASSESS`", skill)
        self.assertEqual(len(list((ROOT / "skills").glob("*/SKILL.md"))), 6)

    def test_no_legacy_layout_references(self):
        for path in ROOT.rglob("*.md"):
            content = path.read_text(encoding="utf-8")
            self.assertNotIn("howto-swt/references", content, str(path))
            self.assertNotIn("evidence-boundaries.md", content, str(path))
        for path in (ROOT / "plugin.json", ROOT / ".codex-plugin/plugin.json"):
            content = path.read_text(encoding="utf-8")
        self.assertIn('"version": "1.2.0"', content)
        self.assertFalse((ROOT / "SWT_MAP_DATA").exists())
        source_data = ROOT.parent / "workspace-docs/source-data/swt-data-source"
        self.assertTrue((source_data / "SWT_MAP_DATA/raw").is_dir())
        self.assertTrue((source_data / "source_manifest.json").is_file())
        self.assertTrue((ROOT / "shared/decision-model.md").is_file())
        self.assertTrue((ROOT / "shared/persistence-contract.md").is_file())
        self.assertTrue((ROOT / "references/user-state.schema.json").is_file())
        self.assertFalse((ROOT / "tests/evals/results").exists())
        for path in (SCRIPTS / "budget.py", SCRIPTS / "state_context.py", SCRIPTS / "sync_shared.py"):
            self.assertNotIn("Path(__file__).resolve().parents[1]", path.read_text(encoding="utf-8"), str(path))

    def test_decision_model_enforces_finite_values_and_safety(self):
        valid = {
            "intent": "CONFLICT", "route": "swt-visa", "supporting_route": "swt-english",
            "stage": "08", "confidence": "high", "risk": "red",
            "evidence_status": "conflicting", "materiality": "critical",
            "missing_information": "safety_blocking", "clarification_level": 4,
            "known_context_keys": ["sponsor_name"], "next_action": "verify_fact",
            "reason_code": "fact_conflict",
        }
        validate_decision(valid)
        invalid_enum = dict(valid, intent="MAKE_UP_A_ROUTE")
        with self.assertRaises(ValueError):
            validate_decision(invalid_enum)
        unsafe = dict(valid, next_action="answer")
        with self.assertRaises(ValueError):
            validate_decision(unsafe)
        wrong_clarification = dict(valid, clarification_level=2)
        with self.assertRaises(ValueError):
            validate_decision(wrong_clarification)

    def test_test_fixtures_contain_no_obvious_personal_identifiers(self):
        fixtures = sorted((ROOT / "tests/evals/fixtures").rglob("*"))
        email = re.compile(r"\b[A-Z0-9._%+-]+@[A-Z0-9.-]+\.[A-Z]{2,}\b", re.I)
        long_number = re.compile(r"\b\d{9,}\b")
        phone = re.compile(r"(?<!\d)(?:\+?\d[\s().-]*){10,}(?!\d)")
        for path in fixtures:
            if not path.is_file():
                continue
            content = path.read_text(encoding="utf-8")
            self.assertIsNone(email.search(content), str(path))
            self.assertIsNone(long_number.search(content), str(path))
            self.assertIsNone(phone.search(content), str(path))

    def test_product_sync_does_not_modify_external_user_state(self):
        with tempfile.TemporaryDirectory() as directory:
            env = os.environ.copy()
            env["USER_DATA_ROOT"] = directory
            state = {"schema_version": "1.0.0", "updated_at": "2026-09-29T01:00:00Z", "profile": {"target_profile": "agency"}}
            save_state(state, env)
            before = (Path(directory) / "swt-user-state.json").read_bytes()
            for script_args in (
                [sys.executable, str(SCRIPTS / "sync_shared.py")],
                [sys.executable, str(SCRIPTS / "validate.py")],
            ):
                result = subprocess.run(script_args, cwd=ROOT, env=env, text=True, capture_output=True, check=False)
                self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
            self.assertEqual((Path(directory) / "swt-user-state.json").read_bytes(), before)
            self.assertEqual(load_state(env), state)
