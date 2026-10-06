# 数据字典 v0.2

本版采用 JSON 记录和 Markdown 资料，不依赖数据库服务。`assets/collection-records.json` 是可复制的采集模板，空数组表示尚无数据，不得把空模板用于推荐。一个事实一条 claim；复杂合同保留原件，以页码引用，不能只留下摘要。

## 公共结构

- `schema_version`：本版为 `0.2`。
- `sources`：来源对象数组。`id` 唯一；`kind` 为 official_rule / contract / written_reply / firsthand / marketing / assumption；`issuer` 出具者；`locator` URL 或相对资料路径；`location` 页码、条款、截图位置；`published_at` 可为 null；`checked_at` 是核验日期或 null；`applicable_year` 项目年度或 null；`scope` 本来源覆盖的对象；`permission` 内部使用／可公开／待确认；`notes` 局限。核验日期不代替适用日期。
- 八类实体数组：`agencies`、`sponsors`、`relationships`、`locations`、`offers`、`cases`、`documents`、`process_events`。
- 每个实体含 `id`、`label`、`claims`。关系也独立建实体，不能从两个名称同页出现就推定关系。
- 每条 claim 含 `field`、`value`、`unit`（无单位为 null）、`applicable_year`、`status`、`source_ids`、`notes`。
- `status` 枚举：verified / pending / conflicting / expired / historical。pending 允许 `value=null` 与无来源；其余状态必须有来源。verified 至少有核验日期，值不能为 null；脚本只检查形式，不能证明真实性。
- 金额必须有币种；周期必须明确每人／每间、小时／周／月／全程。条件、排除项和范围不能省略在 notes 中。空值是未知，0 必须来自明确记录。

## 实体字段

| 实体 | 应收字段（按具体决策补齐） |
|---|---|
| agency | legal_name、brand、product_name、project_year、enrollment_requirements、service_mode、fees、payment_schedule、refund_terms、placement_method、rejection_reapplication_terms、service_scope、response_channels、commercial_relationship |
| sponsor | legal_name、program_category、designation_evidence、project_year、arrival_process、job_change_process、second_job_process、housing_transport_support、routine_contact、emergency_contact |
| relationship | agency_id、sponsor_id、product_name、project_year、relationship_terms、choice_rights、evidence_scope |
| location | state、city、area、project_season、housing_options、grocery_access、transit_routes、last_service_time、support_groups、participant_data、weather_constraints、sales_tax_state、sales_tax_local、income_tax_state、tax_scope |
| offer | agency_id、sponsor_id、location_id、employer_name、job_title、duties、project_year、start_end_dates、hourly_wage、hours_promised、hours_observed、overtime_terms、tips、pay_frequency、first_pay_date、deductions、shift_schedule、housing_terms、commute、vacancy_status、sponsor_confirmation、change_conditions |
| case | anonymous_id、project_year、location_id、offer_id、agency_id、sponsor_id、dates、promised_terms、actual_hours、actual_pay、housing_cost、commute、problem、actions、outcome、second_job_stage、sample_limit、publication_permission |
| document | document_type、owner_scope、project_year、agency_id、sponsor_id、offer_id、issuer、version_date、received_at、submitted_at、reviewed_at、deadline、status、supersedes_document_id、privacy_level、key_field_consistency |
| process_event | stage_id、event_type、occurred_at、deadline_at、timezone、responsible_party、channel、document_id、status、confirmation、blocker、next_action |

这些是采集方向，不是要求每个用户一次提供全部。未收齐时可以开展比较或流程判断，但关联资格、底线、收费、身份字段或阶段门槛等关键缺口不能视为已通过。

`documents` 记录文件本身的对象、版本、处理状态与隐私级别，不复制证件号码、DS-160 编号、SEVIS ID、账号密码、签名或私人联系信息。`process_events` 记录可观察事件，例如“收到 Offer”“提交 DS-160 草稿”“Sponsor 要求更正”“预约确认生成”；不能只写“正在办理”这类无法验证的状态。

## 标识关联与版本

ID 采用稳定英文前缀，例如 agency-001、sponsor-001、offer-001。`agency_id` 等已知外键必须能找到相应实体；未知外键保留 pending/null。同名不同主体或同主体不同年度产品分别记录。

新年度或新报价新增记录，旧记录保留历史状态；不能直接覆盖往届实绩。资料冲突时保留两条带来源的 claim 并标 conflicting。用户明确提供假设时 source.kind=assumption，不能标 verified。

## 原始资料的处理

原件保留只读副本，录入字段后与原件核对；截图同时保留上下文、日期、出具方与条件，先脱敏。不把问卷中的自由文本机械映射到错误的代码名；按实际题目文本确认列。

预算数据另用 `assets/budget-example.json` 的结构，与实体数据分离。每个预算假设通过 `assumptions` 描述来源和适用条件，预算脚本不承担来源核验。
