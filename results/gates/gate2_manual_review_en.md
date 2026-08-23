# GATE 2 — manual review sheet

150 pairs scored. Review the **30 priority pairs** in the order given, then the **20 control pairs**.

**Stop rule.** The priority list is ranked by risk, not thresholded. If you reach 10 consecutive pairs needing no rewrite, stop and record where you stopped. If the last pairs are still producing rewrites, extend past the budget.

Two rules are under review. Neither can be checked by machine.

| Rule | Question to answer on every pair |
| --- | --- |
| **R4** | Does variant B keep the same domain and the same principal entity? |
| **R6** | Is variant B *close but missing* — not off-topic, and not still answerable? |

Mark each row `ok` or `rewrite`. Rewrite in `data/authoring/en/<domain>.jsonl`, then run `make gates`: a rewrite can move the GATE 3 numbers, so both gates must be re-run and the new figures recorded.

---

## Priority pairs, highest risk first

### 1. p1_en_pay_008 · R6 residual-answer

`payroll_benefits` · **Pinecrest Foods** · Shift Premium Standard, Part 2: Night Work  
field `night_premium_pct` -> `weekend_premium_pct` · topic-fit 0.11 · question-pull 0.50 · residual 0.50

**Q** What premium does night shift attract at Pinecrest Foods?

**A** *Night shift attracts a premium of 20 percent above the base hourly rate.* → `20 percent`

**B** *Weekend shifts attract a premium of 35 percent above the base hourly rate.*

**surviving sentence** *Night shift is defined as any shift starting between 22:00 and 04:00.*

> Does the sentence below still answer the question once the evidence is gone? If it does, B is not unanswerable.

verdict: `___`

---

### 2. p1_en_legal_009 · R6 question-pull, R6 residual-answer

`legal_compliance` · **Quillon Media** · Rights and Licensing Handbook, Section 6: Clearance  
field `licence_term_months` -> `territory_count` · topic-fit 0.12 · question-pull 0.75 · residual 0.25

**Q** What is the term of a standard editorial licence at Quillon Media?

**A** *A standard editorial licence runs for a term of 24 months from first publication.* → `24 months`

**B** *A standard editorial licence covers 12 named markets from first publication.*

**surviving sentence** *Quillon Media retains evidence of clearance for the life of the licence plus six years.*

> Is B a fair hard negative, or is it close enough that answering with its figure would be reasonable? If reasonable, rewrite.
> Does the sentence below still answer the question once the evidence is gone? If it does, B is not unanswerable.

verdict: `___`

---

### 3. p1_en_cs_015 · R6 residual-answer

`customer_support` · **Windrow Agritech** · Grower Support Standard, Section 4: Field Visits  
field `field_visit_days` -> `followup_assessment_days` · topic-fit 0.38 · question-pull 0.50 · residual 0.50

**Q** Within how many working days of acceptance is a field visit scheduled at Windrow Agritech?

**A** *A field visit is scheduled within 3 working days of a request being accepted.* → `3 working days`

**B** *A follow-up crop assessment is scheduled 28 working days after a request is accepted.*

**surviving sentence** *Visit outcomes are recorded in the grower record within two working days.*

> Does the sentence below still answer the question once the evidence is gone? If it does, B is not unanswerable.

verdict: `___`

---

### 4. p1_en_itsd_014 · R6 residual-answer

`it_service_desk` · **Vestra Insurance** · Business Continuity Standard, Part 6: Recovery  
field `recovery_time_hours` -> `recovery_point_minutes` · topic-fit 0.38 · question-pull 0.50 · residual 0.50

**Q** What is the recovery time objective for tier one applications at Vestra Insurance?

**A** *Tier one applications carry a recovery time objective of 4 hours.* → `4 hours`

**B** *Tier one applications carry a data loss tolerance of 15 minutes.*

**surviving sentence** *Recovery arrangements are exercised at least once a year for every tier one application.*

> Does the sentence below still answer the question once the evidence is gone? If it does, B is not unanswerable.

verdict: `___`

---

### 5. p1_en_fin_009 · R6 off-topic, R6 residual-answer

`finance_expense` · **Quillon Media** · Corporate Card Rules, Part 2: Limits and Use  
field `corporate_card_limit` -> `cash_advance_limit` · topic-fit 0.00 · question-pull 0.50 · residual 0.25

**Q** What is the standard monthly corporate card limit below director grade at Quillon Media?

**A** *The standard monthly card limit is 6,000 dollars for all cardholders below director grade.* → `6,000 dollars`

**B** *The standard overseas cash advance is 1,500 dollars for all staff below director grade.*

**surviving sentence** *Personal expenditure on a corporate card is repaid within five working days of the statement date.*

> Is B still recognisably about this policy, or has it become filler the model can dismiss on topic alone?
> Does the sentence below still answer the question once the evidence is gone? If it does, B is not unanswerable.

verdict: `___`

---

### 6. p1_en_cs_014 · R6 question-pull, R6 residual-answer

`customer_support` · **Vestra Insurance** · Claims Service Standard, Part 4: Settlement  
field `settlement_days` -> `file_closure_days` · topic-fit 0.33 · question-pull 0.67 · residual 0.33

**Q** Within how many working days of a claim being agreed is settlement made at Vestra Insurance?

**A** *Settlement is made within 10 working days of the claim being agreed.* → `10 working days`

**B** *Claim files are closed 45 working days after the claim is agreed.*

**surviving sentence** *The handler confirms the documentation required within two working days.*

> Is B a fair hard negative, or is it close enough that answering with its figure would be reasonable? If reasonable, rewrite.
> Does the sentence below still answer the question once the evidence is gone? If it does, B is not unanswerable.

verdict: `___`

---

### 7. p1_en_itsd_001 · R6 residual-answer

`it_service_desk` · **Northwind Logistics** · Service Level Agreement, Section 2: Incident Response  
field `p1_response_minutes` -> `major_incident_bridge_minutes` · topic-fit 0.22 · question-pull 0.50 · residual 0.33

**Q** Within how long does the service desk acknowledge a priority one incident at Northwind Logistics?

**A** *The service desk acknowledges a priority one incident within 15 minutes of the ticket being raised.* → `15 minutes`

**B** *The service desk convenes a major incident bridge within 30 minutes of the ticket being raised.*

**surviving sentence** *Northwind Logistics operates the service desk between 06:00 and 22:00 on working days.*

> Does the sentence below still answer the question once the evidence is gone? If it does, B is not unanswerable.

verdict: `___`

---

### 8. p1_en_dg_002 · R6 off-topic, R6 question-pull

`data_governance` · **Bramble Holdings** · Subject Rights Procedure, Part 2: Response  
field `dsar_response_days` -> `registration_days` · topic-fit 0.00 · question-pull 0.83 · residual 0.00

**Q** Within how many days of receipt is a subject access request answered at Bramble Holdings?

**A** *A subject access request is answered within 30 days of receipt.* → `30 days`

**B** *A subject access request is registered within 2 days of receipt.*

> Is B still recognisably about this policy, or has it become filler the model can dismiss on topic alone?
> Is B a fair hard negative, or is it close enough that answering with its figure would be reasonable? If reasonable, rewrite.

verdict: `___`

---

### 9. p1_en_pay_005 · R6 residual-answer

`payroll_benefits` · **Larkspur Retail** · Referral Scheme Rules, Section 2: Awards  
field `referral_bonus_amount` -> `long_service_award` · topic-fit 0.12 · question-pull 0.43 · residual 0.29

**Q** What referral award is paid when the referred candidate completes probation at Larkspur Retail?

**A** *A referral award of 1,000 dollars is paid when the referred candidate completes probation.* → `1,000 dollars`

**B** *A long service award of 500 dollars is paid when an employee completes five years of service.*

**surviving sentence** *Only the first referral of a candidate is eligible where more than one is received.*

> Does the sentence below still answer the question once the evidence is gone? If it does, B is not unanswerable.

verdict: `___`

---

### 10. p1_en_itsd_004 · R6 residual-answer

`it_service_desk` · **Harborview Health** · Backup and Recovery Policy, Part 2: Retention  
field `backup_retention_days` -> `log_forwarding_minutes` · topic-fit 0.14 · question-pull 0.50 · residual 0.25

**Q** For how long are daily system backups retained at Harborview Health?

**A** *Daily system backups are retained for 35 days before they are overwritten.* → `35 days`

**B** *Daily system logs are forwarded to the central platform within 15 minutes.*

**surviving sentence** *Monthly backups are held separately under the archival schedule in Part 3.*

> Does the sentence below still answer the question once the evidence is gone? If it does, B is not unanswerable.

verdict: `___`

---

### 11. p1_en_legal_001 · R6 off-topic, R6 question-pull

`legal_compliance` · **Northwind Logistics** · Records Management Policy, Section 4: Retention Periods  
field `contract_retention_years` -> `contract_review_years` · topic-fit 0.00 · question-pull 0.75 · residual 0.00

**Q** For how long are executed commercial contracts retained at Northwind Logistics?

**A** *Executed commercial contracts are retained for 7 years after the contract ends.* → `7 years`

**B** *Executed commercial contracts are reviewed every 3 years after they are signed.*

> Is B still recognisably about this policy, or has it become filler the model can dismiss on topic alone?
> Is B a fair hard negative, or is it close enough that answering with its figure would be reasonable? If reasonable, rewrite.

verdict: `___`

---

### 12. p1_en_sec_008 · R6 question-pull, R6 residual-answer

`security_access` · **Pinecrest Foods** · Access Request Procedure, Part 2: Approval  
field `access_fulfilment_days` -> `recertification_days` · topic-fit 0.43 · question-pull 0.71 · residual 0.29

**Q** Within how many working days of final approval are access requests fulfilled at Pinecrest Foods?

**A** *Requests are fulfilled within 3 working days of the final approval.* → `3 working days`

**B** *Requests are certified again within 90 working days of final approval.*

**surviving sentence** *Requests that remain unapproved for ten days are cancelled automatically.*

> Is B a fair hard negative, or is it close enough that answering with its figure would be reasonable? If reasonable, rewrite.
> Does the sentence below still answer the question once the evidence is gone? If it does, B is not unanswerable.

verdict: `___`

---

### 13. p1_en_proc_010 · R6 question-pull, R6 residual-answer

`procurement` · **Riverbend Bank** · Third Party Risk Standard, Section 5: Due Diligence  
field `third_party_review_months` -> `remediation_days` · topic-fit 0.50 · question-pull 0.67 · residual 0.33

**Q** How often are high risk third parties reassessed at Riverbend Bank?

**A** *High risk third parties are reassessed every 12 months.* → `every 12 months`

**B** *High risk third parties must remediate within 30 days.*

**surviving sentence** *Riverbend Bank assesses every third party against the risk tiers defined in Section 2.*

> Is B a fair hard negative, or is it close enough that answering with its figure would be reasonable? If reasonable, rewrite.
> Does the sentence below still answer the question once the evidence is gone? If it does, B is not unanswerable.

verdict: `___`

---

### 14. p1_en_legal_005 · R6 question-pull

`legal_compliance` · **Larkspur Retail** · Confidentiality Agreements Standard, Section 2: Term  
field `nda_term_years` -> `nda_notice_months` · topic-fit 0.11 · question-pull 0.80 · residual 0.00

**Q** What is the term of a mutual non-disclosure agreement at Larkspur Retail?

**A** *A mutual non-disclosure agreement runs for a term of 5 years from the effective date.* → `5 years`

**B** *A mutual non-disclosure agreement carries a 3 month notice period from that date.*

> Is B a fair hard negative, or is it close enough that answering with its figure would be reasonable? If reasonable, rewrite.

verdict: `___`

---

### 15. p1_en_fac_005 · R6 off-topic

`facilities_travel` · **Larkspur Retail** · Parking Allocation Procedure, Section 2: Spaces  
field `parking_spaces` -> `bicycle_stands` · topic-fit 0.00 · question-pull 0.33 · residual 0.17

**Q** How many spaces does the head office car park provide at Larkspur Retail?

**A** *The head office car park provides 40 spaces allocated by the facilities team.* → `40 spaces`

**B** *The head office bicycle store provides 24 stands kept by the facilities team.*

> Is B still recognisably about this policy, or has it become filler the model can dismiss on topic alone?

verdict: `___`

---

### 16. p1_en_cs_008 · R6 off-topic

`customer_support` · **Pinecrest Foods** · Consumer Care Procedure, Part 4: Product Complaints  
field `safety_escalation_hours` -> `regulator_notification_hours` · topic-fit 0.00 · question-pull 0.62 · residual 0.00

**Q** Within how long are complaints indicating a food safety risk escalated to technical services at Pinecrest Foods?

**A** *Complaints indicating a food safety risk are escalated to technical services within 1 hour.* → `1 hour`

**B** *Complaints indicating a food safety risk go to the regulator within 24 hours of confirmation.*

> Is B still recognisably about this policy, or has it become filler the model can dismiss on topic alone?

verdict: `___`

---

### 17. p1_en_hr_002 · R6 question-pull

`hr_policy` · **Bramble Holdings** · People Policy 12: Annual Leave  
field `annual_leave_days` -> `leave_carryover_days` · topic-fit 0.38 · question-pull 0.67 · residual 0.22

**Q** How many days of annual leave do employees in grades 5 and above accrue per calendar year at Bramble Holdings?

**A** *Employees in grades 5 and above accrue 22 days of annual leave per calendar year.* → `22 days`

**B** *Employees in grades 5 and above may carry 12 days of leave into the next year.*

> Is B a fair hard negative, or is it close enough that answering with its figure would be reasonable? If reasonable, rewrite.

verdict: `___`

---

### 18. p1_en_proc_005

`procurement` · **Larkspur Retail** · Payment Terms Policy, Part 1: Standard Terms  
field `payment_terms_days` -> `warranty_months` · topic-fit 0.12 · question-pull 0.40 · residual 0.20

**Q** What is the standard payment term for goods suppliers at Larkspur Retail?

**A** *The standard payment term for goods suppliers is 45 days from the date of a valid invoice.* → `45 days`

**B** *The standard warranty period for goods supplied is 24 months from the date of delivery.*


verdict: `___`

---

### 19. p1_en_proc_012 · R6 residual-answer

`procurement` · **Tanager Labs** · Consumables Purchasing Notes, Section 3: Reorder  
field `lead_time_days` -> `consolidation_cycle_days` · topic-fit 0.29 · question-pull 0.43 · residual 0.29

**Q** What standard lead time applies to consumable purchase orders at Tanager Labs?

**A** *Consumable purchase orders are raised with a standard lead time of 14 days.* → `14 days`

**B** *Consumable purchase orders are consolidated into a weekly release every 7 days.*

**surviving sentence** *Tanager Labs holds safety stock for reagents with a lead time longer than one month.*

> Does the sentence below still answer the question once the evidence is gone? If it does, B is not unanswerable.

verdict: `___`

---

### 20. p1_en_sec_005 · R6 residual-answer

`security_access` · **Larkspur Retail** · Physical Security Policy, Section 5: Visitors  
field `visitor_badge_validity` -> `contractor_badge_days` · topic-fit 0.29 · question-pull 0.33 · residual 0.33

**Q** How long is a visitor badge valid at Larkspur Retail?

**A** *A visitor badge is valid for 1 day and expires automatically at midnight.* → `1 day`

**B** *A contractor badge is issued for 30 days and expires automatically at midnight.*

**surviving sentence** *Contractors working for more than one week are issued a temporary staff badge instead.*

> Does the sentence below still answer the question once the evidence is gone? If it does, B is not unanswerable.

verdict: `___`

---

### 21. p1_en_itsd_009 · R6 off-topic

`it_service_desk` · **Quillon Media** · Patch Management Standard, Section 2: Windows  
field `patch_window_hours` -> `resolution_target_hours` · topic-fit 0.00 · question-pull 0.60 · residual 0.00

**Q** How long is the standard maintenance window for production servers at Quillon Media?

**A** *The standard maintenance window for production servers is 4 hours on the second Sunday of the month.* → `4 hours`

**B** *The standard restoration target for production servers is 8 hours from the declared outage.*

> Is B still recognisably about this policy, or has it become filler the model can dismiss on topic alone?

verdict: `___`

---

### 22. p1_en_itsd_011 · R6 off-topic

`it_service_desk` · **Solstice Apparel** · Service Catalogue, Section 7: Resolution Targets  
field `resolution_target_hours` -> `p2_response_hours` · topic-fit 0.00 · question-pull 0.60 · residual 0.00

**Q** What is the resolution target for priority two incidents at Solstice Apparel?

**A** *Priority two incidents carry a resolution target of 12 hours.* → `12 hours`

**B** *Priority two incidents receive a first response in 2 hours.*

> Is B still recognisably about this policy, or has it become filler the model can dismiss on topic alone?

verdict: `___`

---

### 23. p1_en_legal_007 · R6 off-topic

`legal_compliance` · **Oakfield Energy** · Internal Audit Charter, Section 5: Coverage  
field `audit_frequency_months` -> `risk_scoring_months` · topic-fit 0.00 · question-pull 0.60 · residual 0.00

**Q** How often is every high risk process audited at Oakfield Energy?

**A** *Every high risk process is audited at least once every 24 months.* → `every 24 months`

**B** *Every high risk process is scored for risk at least once every 12 months.*

> Is B still recognisably about this policy, or has it become filler the model can dismiss on topic alone?

verdict: `___`

---

### 24. p1_en_legal_003 · R6 question-pull

`legal_compliance` · **Calder Manufacturing** · Speak Up Procedure, Section 3: Handling  
field `whistleblower_response_days` -> `investigation_outcome_days` · topic-fit 0.14 · question-pull 0.75 · residual 0.00

**Q** Within how many working days is a report acknowledged at Calder Manufacturing?

**A** *An acknowledgement is sent to the reporter within 5 working days of a report being received.* → `5 working days`

**B** *An investigation outcome is communicated to the reporter within 40 working days of the report.*

> Is B a fair hard negative, or is it close enough that answering with its figure would be reasonable? If reasonable, rewrite.

verdict: `___`

---

### 25. p1_en_cs_003 · R6 off-topic

`customer_support` · **Calder Manufacturing** · Warranty Terms, Section 3: Standard Cover  
field `warranty_months` -> `service_interval_months` · topic-fit 0.00 · question-pull 0.57 · residual 0.00

**Q** What warranty period applies to machinery sold to commercial customers at Calder Manufacturing?

**A** *Machinery sold to commercial customers carries a warranty of 24 months from commissioning.* → `24 months`

**B** *Machinery sold to commercial customers is serviced at intervals of 12 months from commissioning.*

> Is B still recognisably about this policy, or has it become filler the model can dismiss on topic alone?

verdict: `___`

---

### 26. p1_en_itsd_007 · R6 off-topic

`it_service_desk` · **Oakfield Energy** · Change Management Procedure, Section 5: Freeze Periods  
field `change_freeze_days` -> `patch_window_hours` · topic-fit 0.00 · question-pull 0.57 · residual 0.00

**Q** How long does the change freeze last around each financial period close at Oakfield Energy?

**A** *A change freeze applies for 10 days around each financial period close.* → `10 days`

**B** *A maintenance window of 6 hours applies around each financial period close.*

> Is B still recognisably about this policy, or has it become filler the model can dismiss on topic alone?

verdict: `___`

---

### 27. p1_en_legal_010 · R6 off-topic

`legal_compliance` · **Riverbend Bank** · Regulatory Reporting Procedure, Part 2: Deadlines  
field `reporting_deadline_days` -> `report_retention_months` · topic-fit 0.00 · question-pull 0.57 · residual 0.00

**Q** Within how many business days of period end does Riverbend Bank submit each quarterly return?

**A** *Riverbend Bank submits each quarterly return within 20 business days of the period end.* → `20 business days`

**B** *Riverbend Bank retains each quarterly return for 120 months from the period end.*

> Is B still recognisably about this policy, or has it become filler the model can dismiss on topic alone?

verdict: `___`

---

### 28. p1_en_hr_010 · R6 question-pull

`hr_policy` · **Riverbend Bank** · Recruitment Standards, Section 6: Former Employees  
field `rehire_waiting_days` -> `final_pay_days` · topic-fit 0.22 · question-pull 0.83 · residual 0.00

**Q** How long after their last working day may former employees reapply to Riverbend Bank?

**A** *Former employees may reapply 180 days after their last working day.* → `180 days`

**B** *Former employees receive final pay 30 days after their last working day.*

> Is B a fair hard negative, or is it close enough that answering with its figure would be reasonable? If reasonable, rewrite.

verdict: `___`

---

### 29. p1_en_proc_013 · R6 off-topic

`procurement` · **Umbra Consulting** · Subcontractor Engagement Policy, Part 2: Approval  
field `subcontractor_rate_limit` -> `engagement_duration_days` · topic-fit 0.00 · question-pull 0.56 · residual 0.00

**Q** Above what day rate does a subcontractor engagement require approval from the managing partner at Umbra Consulting?

**A** *Subcontractor day rates above 900 dollars require approval from the managing partner.* → `900 dollars`

**B** *Subcontractor engagements longer than 120 days require approval from the managing partner.*

> Is B still recognisably about this policy, or has it become filler the model can dismiss on topic alone?

verdict: `___`

---

### 30. p1_en_cs_002

`customer_support` · **Bramble Holdings** · Returns Policy, Part 2: Refund Window  
field `refund_window_days` -> `cover_registration_days` · topic-fit 0.25 · question-pull 0.62 · residual 0.12

**Q** Within how many days of delivery may customers return an unused item for a full refund at Bramble Holdings?

**A** *Customers may return an unused item for a full refund within 30 days of delivery.* → `30 days`

**B** *Customers may register an unused item for extended cover within 60 days of delivery.*


verdict: `___`

---

## Control pairs (below the priority cut)

Drawn at random from outside the priority list. Reviewing them is what lets you report a defect rate rather than an impression: if the control sample is clean and the priority list is not, the ranking is working.

### p1_en_legal_011

**Q** How often are approved intermediaries re-screened at Solstice Apparel?

**A** *Approved intermediaries are re-screened every 12 months.* → `every 12 months`

**B** *Approved intermediaries are paid on 30 day terms.*

verdict: `___`

### p1_en_proc_001

**Q** Above what value does a purchase require a competitive tender with at least three bids at Northwind Logistics?

**A** *A competitive tender with at least three bids is required for any purchase above 50,000 dollars.* → `50,000 dollars`

**B** *A single-source justification is required for any purchase above 30,000 dollars in a single order.*

verdict: `___`

### p1_en_pay_009

**Q** Within how many days of receipt does Quillon Media pay a valid freelance invoice?

**A** *Quillon Media pays freelance invoices within 21 days of receipt of a valid invoice.* → `21 days`

**B** *Quillon Media retains commission records for 72 months from receipt of the invoice.*

verdict: `___`

### p1_en_fac_004

**Q** During what hours are administrative buildings open to staff on weekdays at Harborview Health?

**A** *Administrative buildings are open to staff between 06:00 and 20:00 on weekdays.* → `between 06:00 and 20:00`

**B** *Administrative buildings are cleaned by contractors between 21:00 and 23:00.*

verdict: `___`

### p1_en_legal_015

**Q** How far before expiry is a permit renewal application submitted at Windrow Agritech?

**A** *A permit renewal application is submitted 180 days before the expiry date.* → `180 days`

**B** *An independent permit audit is carried out 90 days before the expiry date.*

verdict: `___`

### p1_en_hr_003

**Q** At what rate is overtime worked on a public holiday paid at Calder Manufacturing?

**A** *Overtime worked on a gazetted public holiday is paid at 2.5 times the base hourly rate.* → `2.5 times`

**B** *Certified sick leave for production staff is capped at 26 days in any rolling year.*

verdict: `___`

### p1_en_dg_013

**Q** How often is library content reviewed for currency at Umbra Consulting?

**A** *Content is reviewed for currency every 18 months and withdrawn if superseded.* → `every 18 months`

**B** *Content is tagged against the capability taxonomy every 6 months by the team.*

verdict: `___`

### p1_en_itsd_005

**Q** After how long of inactivity is a virtual private network session terminated at Larkspur Retail?

**A** *A virtual private network session is terminated after 30 minutes of inactivity.* → `30 minutes`

**B** *A virtual private network certificate is reissued every 24 months per device.*

verdict: `___`

### p1_en_pay_003

**Q** What is the waiting period before new employees join the health plan at Calder Manufacturing?

**A** *New employees join the health plan after a waiting period of 90 days.* → `90 days`

**B** *New employees qualify for an annual wellbeing allowance of 600 dollars.*

verdict: `___`

### p1_en_hr_005

**Q** How many weeks of paid parental leave are primary caregivers entitled to at Larkspur Retail?

**A** *Primary caregivers are entitled to 18 weeks of paid parental leave at full salary.* → `18 weeks`

**B** *Primary caregivers become eligible for an internal transfer after 24 months in grade.*

verdict: `___`

### p1_en_dg_006

**Q** What data quality score triggers a remediation plan at Meridian Systems?

**A** *A data quality score below 95 percent triggers a remediation plan.* → `below 95 percent`

**B** *A data completeness score is recalculated every 14 days per domain.*

verdict: `___`

### p1_en_dg_012

**Q** For how long are project datasets archived after project completion at Tanager Labs?

**A** *Project datasets are archived for 10 years after project completion.* → `10 years`

**B** *Project datasets are assessed for value 3 years after project completion.*

verdict: `___`

### p1_en_pay_010

**Q** Over what period do deferred awards vest at Riverbend Bank?

**A** *Deferred awards vest over 3 years in equal annual instalments.* → `3 years`

**B** *Deferred awards remain subject to clawback for 7 full years.*

verdict: `___`

### p1_en_fin_005

**Q** What is the mileage rate for private vehicle use on company business at Larkspur Retail?

**A** *The mileage rate for use of a private vehicle on company business is 58 cents per kilometre.* → `58 cents`

**B** *The daily allowance for meals taken on company business is 40 dollars per working day.*

verdict: `___`

### p1_en_hr_006

**Q** How often are formal performance reviews held for permanent employees at Meridian Systems?

**A** *Formal performance reviews are held every 6 months for all permanent employees.* → `every 6 months`

**B** *Probation may be extended once by a further 30 days for all permanent employees.*

verdict: `___`

### p1_en_proc_015

**Q** What is the standard warranty period for capital equipment at Windrow Agritech?

**A** *Capital equipment carries a standard warranty period of 36 months from acceptance.* → `36 months`

**B** *Capital equipment is revalued for insurance purposes every 24 months from acceptance.*

verdict: `___`

### p1_en_fac_006

**Q** By what time must a desk booking be claimed at Meridian Systems?

**A** *A desk booking is released automatically if it is not claimed by 10:30.* → `10:30`

**B** *A desk booking may be cancelled without penalty until 08:00 on the day of use.*

verdict: `___`

### p1_en_dg_001

**Q** How long after the last commercial interaction is customer personal data deleted at Northwind Logistics?

**A** *Customer personal data is deleted 36 months after the last commercial interaction.* → `36 months`

**B** *Customer personal data is checked for accuracy 18 months after the last call.*

verdict: `___`

### p1_en_pay_014

**Q** After what deferred period does benefit become payable at Vestra Insurance?

**A** *Benefit becomes payable after a deferred period of 26 weeks.* → `26 weeks`

**B** *Benefit is paid at a level of 60 percent of base salary.*

verdict: `___`

### p1_en_fin_008

**Q** What proportion of expense claims does internal audit review each quarter at Pinecrest Foods?

**A** *Internal audit reviews a random sample of 5 percent of all expense claims each quarter.* → `5 percent`

**B** *Internal audit tolerates a budget variance of 3 percent before a formal review is triggered.*

verdict: `___`
