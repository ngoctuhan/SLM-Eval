Thiết kế nghiên cứu

**Đo suy giảm siêu nhận thức khi thu nhỏ mô hình ngôn ngữ**

*Knowing What You Don’t Know Shrinks Faster Than Knowing: Metacognitive Degradation in 4B–14B Language Models on Enterprise Tasks*

| Trường | Giá trị |
| :---- | :---- |
| Phiên bản | 1.0 |
| Trạng thái | Design spec — chờ pilot xác thực |
| Phạm vi mô hình | 4B, 8B, 14B (self-host) \+ 3 API frontier |
| Quyết định chờ | Go/no-go sau pilot 2 tuần (Mục 6\) |

# **Mục lục**

# **0\. Tóm tắt điều hành**

Benchmark hiện tại đo **model làm được gì**. Tài liệu này thiết kế một benchmark để đo **model có biết khi nào nó không làm được không** — và cách năng lực đó suy giảm khi thu nhỏ mô hình.

**Luận điểm trung tâm:**

Khi thu nhỏ mô hình, năng lực siêu nhận thức (metacognition) suy giảm nhanh hơn năng lực tác vụ (task capability). Đây là lý do điểm benchmark không dự đoán được hiệu quả trong sản xuất.

Nếu luận điểm đúng, nó giải thích một nghịch lý đang tồn tại: SLM ghi điểm cao trên benchmark công khai nhưng vỡ trận khi triển khai thật.

Ba trụ thí nghiệm kiểm chứng luận điểm từ ba góc độc lập:

| Trụ | Câu hỏi | Metric mới |
| :---- | :---- | :---- |
| P1 — Discriminative Abstention | Model từ chối vì hiểu context thiếu thông tin, hay vì bất lực? | DAS, Blind Abstention Rate, Abstention AUC |
| P2 — Composition Penalty | Lỗi khi ghép chuỗi tác vụ tích lũy theo cấp số nhân hay tệ hơn? | CPI (Composition Penalty Index) |
| P3 — Self-Deferral Calibration | SLM có tự nhận biết ca khó để escalate lên model lớn? | AURC, Oracle Gap, Cost-per-Correct |

Tiếng Việt **không phải** luận điểm chính. Nó là biến thí nghiệm (robustness check): *cliff có dịch chuyển theo ngôn ngữ không?*

# **1\. Vấn đề và khoảng trống**

## **1.1 Bối cảnh triển khai**

Doanh nghiệp đứng trước lựa chọn: self-host SLM 4B–14B, hay gọi API frontier model. Quyết định này hiện dựa vào bảng điểm benchmark, nhưng bảng điểm không trả lời được ba câu hỏi thực tế:

1. Model có im lặng bịa ra câu trả lời khi tài liệu không chứa thông tin?

2. Model có giữ được độ chính xác khi ghép vào pipeline nhiều bước?

3. Model có tự biết escalate ca khó, hay cần router riêng?

## **1.2 Vị trí so với công trình đã có**

Khảo sát cho thấy các trục sau **đã bị chiếm**, cần kế thừa thay vì làm lại:

| Công trình | Đã làm gì | Ta kế thừa gì |
| :---- | :---- | :---- |
| RGB | Bốn năng lực: noise robustness, negative rejection, information integration, counterfactual resistance | Taxonomy nhiễu |
| AbstentionBench | 20 dataset, 6 kịch bản abstention | Định nghĩa abstention, baseline |
| Magic Mushroom | 4 loại retrieval noise, \~11k cặp QA, cấu hình nhiễu linh hoạt | Bộ sinh distractor |
| BFCL v1–v4 | AST matching, irrelevance detection (từ V2), multi-turn (V3), agentic (V4) | Format tool-call, IrrelAcc |
| SLM-Bench | 15 SLM × 9 task × 4 cấu hình HW, 11 metric gồm cost/sustainability | Giao thức đo hiệu năng |
| LoRA Land | 310 model fine-tune, SLM vượt GPT-4 trên \~80% task | Kết luận đã đóng — **không lặp lại** |
| VMLU, ViLLM-Eval, VLegal-Bench | Benchmark tiếng Việt, chủ yếu trắc nghiệm học thuật và pháp lý | Baseline tiếng Việt |

**Khoảng trống chính xác mà ta chiếm.** Mọi benchmark abstention hiện có báo cáo tỉ lệ từ chối như một con số đơn. Nhưng một tỉ lệ từ chối cao có hai nguyên nhân trái ngược nhau về bản chất:

* **Từ chối có hiểu biết** — model nhận ra context không chứa đáp án.

* **Từ chối do bất lực** — model không xử lý được ngữ nghĩa nên từ chối bừa.

Đây không phải suy đoán. Nghiên cứu về prompt sensitivity đã chỉ ra rằng phương sai gần bằng 0 ở model rất nhỏ **không** thể hiện tính ổn định, mà thể hiện thất bại hệ thống trong việc xử lý tín hiệu ngữ nghĩa. Cùng logic đó áp cho abstention: **một con số abstention đẹp ở model 4B có thể là artifact, không phải năng lực.**

Chưa có benchmark nào tách được hai trường hợp này. Đó là đóng góp phương pháp của P1.

Tương tự, P2 và P3 nhắm vào hai giả định chưa ai kiểm chứng:

* **P2:** benchmark task đơn lẻ dự đoán được hiệu năng pipeline (giả định tính độc lập của lỗi).

* **P3:** kiến trúc cascade khả thi vì SLM tự biết escalate.

## **1.3 Câu hỏi nghiên cứu**

| Mã | Câu hỏi |
| :---- | :---- |
| RQ1 | Tỉ lệ abstention có phản ánh năng lực phân biệt answerable/unanswerable, và mối quan hệ này thay đổi thế nào theo kích thước mô hình? |
| RQ2 | Độ chính xác của chuỗi tác vụ có bằng tích độ chính xác các bước độc lập? Sai lệch (nếu có) có phụ thuộc kích thước mô hình? |
| RQ3 | Tín hiệu tự tin nội sinh của SLM có đủ để làm router trong cascade, và khoảng cách tới router lý tưởng là bao nhiêu? |
| RQ4 | Các hiệu ứng trên có dịch chuyển giữa tiếng Anh và tiếng Việt? |

# **2\. Trụ 1 — Discriminative Abstention**

## **2.1 Thiết kế cặp sinh đôi (paired twin design)**

Mỗi item trong bộ dữ liệu là **một cặp**, không phải một mẫu đơn:

* **Bản A (answerable):** câu hỏi Q \+ context C chứa mệnh đề trả lời được Q.

* **Bản B (unanswerable):** câu hỏi Q y hệt \+ context C′, trong đó mệnh đề chứa đáp án đã bị **thay thế** bằng nội dung cùng chủ đề, cùng độ dài, cùng thanh ngữ.

Nguyên tắc bất biến bắt buộc giữa A và B:

| Thuộc tính | Yêu cầu |
| :---- | :---- |
| Câu hỏi | Giống hệt từng ký tự |
| Số chunk | Bằng nhau |
| Độ dài context (token) | Lệch ≤ 5% |
| Chủ đề bề mặt | Cùng domain, cùng thực thể chính |
| Vị trí mệnh đề bị đổi | Phân bố đều (đầu / giữa / cuối) |

**Điểm mấu chốt:** B phải là *"gần đúng nhưng thiếu"*, không phải *"lạc đề"*. Nếu B lạc đề, task trở thành phát hiện chủ đề — quá dễ, không đo được gì.

## **2.2 Kiểm định rò rỉ tín hiệu bề mặt (shortcut audit)**

Đây là bước xác thực bắt buộc; thiếu nó thì P1 vô giá trị. Nếu A và B khác nhau ở đặc trưng bề mặt, model có thể phân biệt mà không cần hiểu.

**Giao thức:**

1. Huấn luyện một classifier TF-IDF \+ logistic regression để phân biệt A/B **chỉ từ context**, không có câu hỏi.

2. Đo AUC bằng cross-validation 5-fold.

3. **Ngưỡng chấp nhận: AUC ≤ 0.60.** Nếu vượt, phải viết lại các cặp bị rò rỉ.

4. Bổ sung: hai annotator người thử phân biệt A/B trong 10 giây mỗi mẫu mà không đọc câu hỏi — tỉ lệ đúng phải xấp xỉ ngẫu nhiên.

Ghi báo cáo con số AUC này vào paper. Đây là bằng chứng cho thấy thiết kế cặp là hợp lệ.

## **2.3 Định nghĩa metric**

Với mỗi cặp (A, B), mô hình cho ra kết quả thuộc một trong bốn ô:

|  | Đúng trên A | Sai / abstain trên A |
| :---- | :---- | :---- |
| **Abstain trên B** | ✅ Discriminative | ⚠️ Blind abstention |
| **Trả lời trên B** | ❌ Overconfident | ❌ Incompetent |

DAS  (Discriminative Abstention Score) \= P(correct(A) ∧ abstain(B))  
BAR  (Blind Abstention Rate)           \= P(abstain(A) ∧ abstain(B))  
OCR  (Overconfidence Rate)             \= P(correct(A) ∧ answer(B))  
NAR  (Naive Abstention Rate)           \= P(abstain(B))     \<- metric cũ

**Chỉ số quan trọng nhất của paper:** khoảng cách giữa NAR và DAS theo kích thước mô hình.

Giả thuyết **H1**: NAR(4B) ≈ NAR(14B) nhưng DAS(4B) \<\< DAS(14B), với BAR(4B) \>\> BAR(14B).

Nếu H1 đúng: **benchmark abstention hiện hành cho điểm sai cho model nhỏ.** Đó là finding có sức nặng.

## **2.4 Biến điều khiển bổ sung**

Chạy P1 dưới hai điều kiện nhiễu để có đường cong thay vì một điểm:

* **Số distractor k ∈ {0, 2, 5, 10}** — chèn chunk nhiễu vào cả A và B.

* **Cường độ chỉ dẫn abstain:** prompt trung tính (không nói gì) so với prompt có chỉ dẫn rõ ("nếu tài liệu không chứa thông tin, trả lời chính xác: KHÔNG CÓ THÔNG TIN"). Chênh lệch giữa hai điều kiện đo mức độ SLM cần được cầm tay chỉ việc — con số này trực tiếp hữu dụng cho người triển khai.

## **2.5 Cách chấm abstention**

Không dùng regex đơn thuần (dễ sai với câu trả lời lửng lơ kiểu *"tài liệu có đề cập nhưng không rõ…"*). Quy trình ba tầng:

1. **Tầng 1 — khớp mẫu chuẩn:** nếu prompt yêu cầu output cố định (KHÔNG CÓ THÔNG TIN), khớp chính xác.

2. **Tầng 2 — classifier nhỏ:** fine-tune một encoder nhẹ trên 300 output đã gán nhãn tay thành ba lớp {abstain, answer, hedge}.

3. **Tầng 3 — kiểm tra chéo bằng người:** 200 mẫu, hai annotator, báo cáo Cohen’s κ giữa classifier và người. Yêu cầu κ ≥ 0.75.

Xử lý **hedge** (nửa vời) là một lớp riêng, không gộp vào abstain. Tỉ lệ hedge theo model size là một sub-finding đáng báo cáo.

# **3\. Trụ 2 — Composition Penalty**

Đây là trụ có xác suất ra kết quả thú vị cao nhất, và rẻ nhất để đo.

## **3.1 Ý tưởng**

Benchmark đo task nguyên tử. Sản xuất chạy chuỗi. Nếu lỗi các bước độc lập, độ chính xác chuỗi bằng tích các độ chính xác. Câu hỏi: **thực tế có đúng vậy không, và sai lệch có phụ thuộc kích thước mô hình?**

## **3.2 Thiết kế chuỗi có kiểm soát**

Xây các chuỗi độ sâu d \= 1, 2, 3, 4 từ một tập **bước nguyên tử** có độ khó đã hiệu chỉnh. Ví dụ chuỗi d=4 cho tình huống nghiệp vụ:

Bước 1 — Relevance:  Trong 6 chunk, chunk nào liên quan tới câu hỏi?  
Bước 2 — Extract:    Từ chunk đã chọn, trích ra 3 trường thông tin.  
Bước 3 — Compute:    Từ 3 trường đó, tính giá trị dẫn xuất (vd: tiền phạt).  
Bước 4 — Format:     Xuất kết quả theo JSON schema cho trước.

**Yêu cầu thiết kế cốt tử — hiệu chỉnh độ khó nguyên tử.** Các bước phải có độ khó tương đương khi đo độc lập, nếu không CPI sẽ lẫn với hiệu ứng "bước 3 vốn khó hơn bước 1". Quy trình hiệu chỉnh:

1. Tạo dư thừa biến thể cho mỗi bước (khoảng 3× số cần thiết).

2. Đo accuracy độc lập trên một model tham chiếu (chọn model 8B).

3. Chỉ giữ các biến thể có accuracy nằm trong dải hẹp, ví dụ 0.78–0.88.

4. Ghép chuỗi từ pool đã hiệu chỉnh.

## **3.3 Hai chế độ đo**

| Chế độ | Cách chạy | Dùng để |
| :---- | :---- | :---- |
| Isolated (teacher-forced) | Mỗi bước chạy riêng, input là **gold output** của bước trước | Ước lượng pᵢ |
| Chained (free-running) | Model tự dùng output của chính nó làm input bước sau | Đo accuracy chuỗi thực P\_obs |

## **3.4 Định nghĩa CPI**

P\_indep(d) \= ∏ (i=1→d) pᵢ            (dự đoán dưới giả định độc lập)  
   
CPI(d)     \= ( P\_indep(d) − P\_obs(d) ) / P\_indep(d)

Đọc kết quả:

* CPI ≈ 0 → lỗi độc lập; benchmark task đơn lẻ **dự đoán được** hiệu năng pipeline.

* CPI \> 0 → có composition penalty; benchmark hiện hành **lạc quan quá mức**.

* CPI \< 0 (super-composition) → có thể xảy ra khi các bước tương quan trên item dễ. Phải báo cáo trung thực, không bỏ qua.

Giả thuyết **H2**: CPI(d) tăng theo d, và với cùng d thì CPI(4B) \> CPI(8B) \> CPI(14B) \> CPI(API).

## **3.5 Ablation phân tách nguyên nhân**

CPI dương có thể do ba nguyên nhân khác nhau. Cần tách:

| Ablation | Cách làm | Phân tách được gì |
| :---- | :---- | :---- |
| Gold injection tại bước j | Cho model chạy chuỗi nhưng tiêm gold output ở bước j | Lỗi lan truyền vs năng lực bước j suy giảm |
| Context load control | Chạy bước j đơn lẻ nhưng nhồi thêm text vô nghĩa cho bằng độ dài chuỗi | Tách hiệu ứng context dài khỏi hiệu ứng ghép nối |
| Error recovery | Tiêm chủ ý output sai ở bước j−1 | Model có phát hiện và sửa, hay nhận bừa? |

Ablation thứ ba (**error recovery**) đặc biệt giá trị: nó nối P2 về lại luận điểm siêu nhận thức. Model lớn có thể phát hiện input bước trước bị sai; model nhỏ tin tưởng tuyệt đối. Nếu định lượng được điều này, ba trụ hội tụ về một câu chuyện thống nhất.

# **4\. Trụ 3 — Self-Deferral Calibration**

## **4.1 Ý tưởng**

Kiến trúc cascade (SLM xử lý phần lớn, escalate ca khó lên frontier model) đang được dùng rộng rãi. Nó giả định SLM **tự biết** ca nào khó. Giả định này gần như chưa được benchmark.

## **4.2 Ba tín hiệu tự tin cần so sánh**

| Tín hiệu | Cách lấy | Chi phí |
| :---- | :---- | :---- |
| Verbalized confidence | Yêu cầu model xuất điểm 0–100 kèm câu trả lời | Gần như 0 |
| Token logprob | Trung bình logprob của token sinh ra (chỉ có với self-host) | 0 |
| Self-consistency | Sinh n=5 mẫu ở t=0.7, đo tỉ lệ đồng thuận | 5× |

So sánh cả ba là một đóng góp thực tiễn: nếu verbalized confidence gần bằng self-consistency, người triển khai tiết kiệm được 5× chi phí.

## **4.3 Metric**

Vẽ **coverage–risk curve**: sắp xếp item theo độ tự tin giảm dần, cắt bỏ dần các ca kém tự tin nhất, đo accuracy phần còn lại.

AURC         \= Area Under Risk–Coverage curve   (càng thấp càng tốt)  
Oracle Gap   \= AURC(model signal) − AURC(oracle sorting)  
Cost/Correct \= (n\_SLM × cost\_SLM \+ n\_esc × cost\_API) / n\_correct

**Oracle Gap** là con số quan trọng: nó nói model còn cách router lý tưởng bao xa, tức có nên đầu tư xây router riêng hay không.

Giả thuyết **H3**: Oracle Gap tăng khi model nhỏ đi — nghĩa là model càng nhỏ càng cần router ngoài, và chi phí router này thường bị bỏ khỏi bài toán ROI của cascade.

## **4.4 Đầu ra dạng doanh nghiệp cần**

Bảng cuối cùng của trụ này phải đọc được như sau:

Cascade với 8B tự-defer đạt 94.1% accuracy ở escalation rate 22%, chi phí 0.31× so với gọi API toàn bộ. Router ngoài chỉ cải thiện thêm 1.5 điểm — không đáng đầu tư ở quy mô này.

# **5\. Vai trò của tiếng Việt (RQ4)**

Tiếng Việt là **biến thí nghiệm**, không phải claim chính. Điều này biến "bản Việt hóa" từ điểm yếu thành thiết kế hợp lệ.

**Giao thức song song:**

1. Xây bộ dữ liệu ở **cả hai ngôn ngữ**, cùng cấu trúc, cùng thiết kế cặp.

2. Với phần dịch: dịch bởi người, không dùng máy. Kiểm tra ngược (back-translation review) bởi annotator thứ hai.

3. Với phần tiếng Việt gốc: dùng tài liệu nghiệp vụ Việt Nam thật (đã ẩn danh) — đây là phần chống contamination.

4. Đo **language shift**: Δ \= metric(EN) − metric(VI) cho từng model size.

Giả thuyết **H4**: cliff dịch chuyển sớm hơn khoảng một nấc kích thước ở tiếng Việt (tức 8B ở VI hành xử như 4B ở EN), do token hóa kém hiệu quả hơn và dữ liệu instruction-tuning tiếng Việt ít hơn.

Nếu H4 đúng: đây là kết quả có ý nghĩa thực tiễn trực tiếp cho mọi doanh nghiệp Việt Nam đang chọn model — và là claim mới, không phải bản dịch.

# **6\. Pilot 2 tuần — cổng quyết định**

**Không cam kết 10 tuần trước khi biết hiệu ứng có tồn tại.**

## **6.1 Phạm vi pilot**

| Trụ | Quy mô | Tiêu chí thành công |
| :---- | :---- | :---- |
| P1 | 60 cặp (EN, một domain) | DAS(4B) thấp hơn DAS(14B) ≥ 10 điểm **trong khi** NAR lệch ≤ 5 điểm |
| P2 | 40 chuỗi × d ∈ {1,2,3,4} | CPI(4B) − CPI(14B) ≥ 0.10 tại d=3 hoặc d=4 |
| P3 | dùng lại data P1 | Coverage–risk curve của 14B dốc rõ; Oracle Gap(4B) \> Oracle Gap(14B) |

**Cấu hình pilot:** 3 model (4B, 14B, 1 API), 1 prompt, 1 seed, tiếng Anh trước.

**Nguồn lực:** khoảng 4–6 GPU-hour, \~20 USD API, \~5 ngày công tạo dữ liệu.

## **6.2 Bảng quyết định**

| Kết quả pilot | Hành động |
| :---- | :---- |
| Hiệu ứng rõ ở ≥ 2 trụ | Đủ cho paper. Mở rộng theo kế hoạch đầy đủ (Mục 7). |
| Rõ ở 1 trụ | Workshop paper hoặc arXiv preprint \+ open-source harness. Vẫn đáng làm. |
| Không trụ nào rõ | Chuyển hoàn toàn sang open-source harness \+ bài viết kỹ thuật. Đã tiết kiệm 8 tuần. |

Ghi lại bảng này **trước khi** chạy pilot và cam kết tuân theo. Đây là cách tránh bẫy tự thuyết phục mình rằng kết quả nhạt vẫn "có gì đó".

# **7\. Kế hoạch đầy đủ (sau khi pilot vượt cổng)**

| Tuần | Việc | Đầu ra |
| :---- | :---- | :---- |
| 1–2 | Pilot (Mục 6\) | Quyết định go/no-go |
| 3–5 | Mở rộng dữ liệu: P1 200 cặp × 2 ngôn ngữ; P2 120 chuỗi; shortcut audit | Dataset freeze v1 \+ báo cáo AUC, κ |
| 6 | Hoàn thiện harness: adapter đa model, scorer, báo cáo tự động | Repo chạy được end-to-end |
| 7–8 | Chạy full matrix: 6 model × 3 trụ × 3 prompt × 3 seed × 2 ngôn ngữ | results/raw/ đầy đủ |
| 9 | Ablation P2 (gold injection, context load, error recovery) | Bảng phân tách nguyên nhân |
| 10 | Error taxonomy thủ công: 50 lỗi/model, 6 lớp | Hình stacked-bar chủ lực |
| 11–12 | Viết paper \+ dọn repo để release | Bản nháp submit |

## **7.1 Ma trận thí nghiệm**

* **Model:** 4B, 8B, 14B (self-host, ghi rõ quantization) \+ 3 API (OpenAI, Gemini, DeepSeek).

* **Kiểm soát bắt buộc:** cùng system prompt; tắt tool/web search của API model; temperature=0 cho task có đáp án đúng; t=0.7, n=5 cho self-consistency; fix seed; ≥3 lần chạy, báo mean ± std; ghi model\_version\_string \+ timestamp mọi lần gọi API.

* **Kiểm soát quantization:** thêm một cấu hình so sánh **14B-INT4 vs 8B-FP16 ở cùng VRAM** — đây là câu hỏi mà người triển khai thực sự đối mặt.

# **8\. Kiến trúc harness**

Harness này cần thiết trong **cả hai** kịch bản (paper hoặc open-source), nên làm sớm là không lãng phí.

slm-metacog/  
├── data/  
│   ├── p1\_paired/{en,vi}/test.jsonl  
│   ├── p2\_chains/{en,vi}/test.jsonl  
│   └── p3\_deferral/            \# dẫn xuất từ p1  
├── prompts/{p1,p2,p3}/{v1,v2,v3}.txt  
├── adapters/  
│   ├── base.py                 \# interface thống nhất  
│   ├── vllm\_openai.py          \# self-host qua OpenAI-compatible  
│   └── api\_{openai,gemini,deepseek}.py  
├── runners/  
│   ├── run\_paired.py  
│   ├── run\_chain.py            \# isolated \+ chained \+ gold-injection  
│   └── run\_deferral.py  
├── scorers/  
│   ├── abstain\_classifier.py   \# 3 lớp: abstain/answer/hedge  
│   ├── chain\_scorer.py         \# tính pᵢ, P\_obs, CPI  
│   └── deferral.py             \# coverage-risk, AURC, oracle gap  
├── validation/  
│   ├── shortcut\_audit.py       \# TF-IDF AUC cho cặp A/B  
│   └── judge\_agreement.py      \# κ giữa classifier và người  
├── results/raw/\*.jsonl         \# LƯU RAW OUTPUT, không chỉ điểm  
└── analysis/  
    ├── fig\_cliff.py            \# metric theo model size  
    ├── fig\_das\_vs\_nar.py       \# hình chủ lực của paper  
    └── fig\_pareto.py

**Nguyên tắc kỹ thuật:**

* Mọi model — self-host hay API — đi qua **một interface OpenAI-compatible duy nhất**. Code không phân biệt.

* **Luôn lưu raw output**, không chỉ điểm số. Error taxonomy ở tuần 10 phụ thuộc vào việc này; chạy lại toàn bộ là rất tốn.

* Cấu hình thí nghiệm ở file YAML, không hardcode. Mỗi lần chạy sinh một run\_id \+ snapshot config.

## **8.1 Schema dữ liệu**

**P1 — cặp sinh đôi:**

{  
  "pair\_id": "p1\_hr\_0042",  
  "question": "Thời gian thử việc tối đa cho vị trí quản lý là bao lâu?",  
  "variant\_a": {  
    "contexts": \[{"chunk\_id": "c1", "text": "..."}\],  
    "gold\_answer": "60 ngày",  
    "evidence\_chunk\_id": "c1"  
  },  
  "variant\_b": {  
    "contexts": \[{"chunk\_id": "c1", "text": "..."}\],  
    "gold\_answer": null,  
    "removed\_proposition": "Thời gian thử việc với vị trí quản lý không quá 60 ngày.",  
    "replacement\_strategy": "same\_topic\_different\_field"  
  },  
  "meta": {"domain": "hr", "lang": "vi", "n\_distractors": 0,  
           "token\_len\_a": 512, "token\_len\_b": 508, "source": "internal\_doc\_17"}  
}

**P2 — chuỗi:**

{  
  "chain\_id": "p2\_finance\_0011",  
  "depth": 3,  
  "steps": \[  
    {"step": 1, "type": "relevance", "input\_ref": "chain\_input",  
     "gold\_output": \["c3"\], "calibrated\_acc\_8b": 0.84},  
    {"step": 2, "type": "extract", "input\_ref": "step\_1\_output",  
     "gold\_output": {"amount": 1500000, "rate": 0.05, "days": 30},  
     "calibrated\_acc\_8b": 0.81},  
    {"step": 3, "type": "compute", "input\_ref": "step\_2\_output",  
     "gold\_output": {"penalty": 2250000}, "calibrated\_acc\_8b": 0.86}  
  \],  
  "meta": {"domain": "finance", "lang": "vi"}  
}

# **9\. Cấu trúc paper**

| Section | Nội dung | Nguồn |
| :---- | :---- | :---- |
| 1\. Introduction | Nghịch lý benchmark-vs-production; luận điểm metacognition; 4 finding chính | — |
| 2\. Related Work | RGB, AbstentionBench, Magic Mushroom, BFCL, SLM-Bench — và **chính xác cái gì chúng không đo** | Mục 1.2 |
| 3\. Framework | Định nghĩa hình thức DAS/BAR/CPI/AURC; lý do paired design | Mục 2–4 |
| 4\. Dataset Construction | Nguồn, ẩn danh, quy trình paired, **shortcut audit AUC**, κ annotator | Mục 2.2, 5 |
| 5\. Experimental Setup | Model, quantization, decoding, kiểm soát prompt, hạ tầng | Mục 7.1 |
| 6\. Results | DAS vs NAR (hình chủ lực), CPI theo depth × size, coverage–risk | Mục 7 |
| 7\. Analysis | Ablation P2, error taxonomy, language shift EN/VI | Mục 3.5, 5 |
| 8\. Deployment Implications | Bảng "task → size tối thiểu"; cascade có khả thi không; Oracle Gap | Mục 4.4 |
| 9\. Limitations | API model không reproducible; 2 ngôn ngữ; domain hẹp; abstention scorer là proxy | — |

**Contribution statement** (viết thành bốn gạch đầu dòng — reviewer đọc phần này để quyết định):

1. Chỉ ra rằng abstention rate — metric chuẩn hiện hành — **không phân biệt** được năng lực và bất lực, và đề xuất paired design để tách.

2. Định lượng composition penalty và cho thấy benchmark task đơn lẻ lạc quan quá mức bao nhiêu ở từng kích thước mô hình.

3. Benchmark đầu tiên đo tính khả thi của cascade từ phía self-deferral của SLM, kèm Oracle Gap.

4. Bộ dữ liệu song song EN/VI trên tài liệu nghiệp vụ chưa công khai, kèm harness mở.

# **10\. Rủi ro và cách phòng**

| Rủi ro | Mức | Phòng ngừa |
| :---- | :---- | :---- |
| Pilot ra kết quả phẳng | Trung bình | Đã có bảng quyết định Mục 6.2; chi phí chỉ 2 tuần |
| Cặp A/B rò rỉ tín hiệu bề mặt | **Cao** | Shortcut audit bắt buộc, ngưỡng AUC ≤ 0.60; đây là rủi ro số 1 của P1 |
| Không hiệu chỉnh được độ khó nguyên tử ở P2 | Cao | Tạo dư 3× biến thể rồi lọc theo dải accuracy; báo cáo dải thực đạt |
| CPI lẫn với hiệu ứng context dài | Trung bình | Ablation context-load control (Mục 3.5) |
| Trùng lặp với VN-Bench v1 | Trung bình | VN-Bench công bố đang curate contract extraction, official-document parsing, OCR, EN/VN code-switching. **Liên hệ họ trước khi bắt đầu** |
| Không tiếp cận được dữ liệu DN thật | **Cao** | Nếu không có: bỏ claim contamination, giữ nguyên 3 trụ (chúng không phụ thuộc dữ liệu độc quyền), dùng corpus công khai \+ tài liệu tự tạo |
| API model đổi phiên bản giữa kỳ | Thấp | Ghi version string \+ timestamp mọi lần gọi; nêu trong Limitations |

# **11\. Việc cần làm ngay (tuần này)**

1. **Đọc kỹ 3 paper baseline:** RGB, AbstentionBench, SLM-Bench. Đây là ba công trình bạn buộc phải trả lời "khác ở đâu" trong Section 2\.

2. **Liên hệ nhóm VN-Bench** (nrl.ai) để phân định phạm vi hoặc hợp tác. Phát hiện trùng lặp sau khi submit là tình huống tệ nhất.

3. **Chốt câu hỏi dữ liệu:** có tiếp cận được tài liệu nghiệp vụ Việt Nam thật không? Câu trả lời quyết định RQ4 và phần contamination.

4. **Dựng 20 cặp sinh đôi bằng tay** và chạy shortcut audit ngay trên 20 cặp đó. Nếu AUC đã \> 0.6 ở quy mô nhỏ, cần sửa quy trình tạo cặp trước khi mở rộng.

Việc số 4 là việc rẻ nhất mang lại nhiều thông tin nhất. Làm nó trước.