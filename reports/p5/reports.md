# Customer Feedback — P5 Insight Report

Generated: 2026-11-04T15:02:22.848295+00:00

Root causes remain hypotheses until reviewed. Citation checks measure traceability only.

## Input limitations

- Missing sentiment: expected one of sentiment.parquet, sentiment.csv
- P4 indexed only the first 1000 of 393578 cleaned reviews.
- Source files were exported without edits.
- No standalone sentiment.parquet is supplied by current branches; labels come from ratings.
- P3 priority growth and P2 trend growth use different windows and denominators.

## Insight tổng hợp

Phân tích hồi cứu dữ liệu review 1999–2012. Số liệu nhóm lấy từ toàn bộ output P3; bằng chứng P4 giới hạn ở 1.000 review đầu. Review đại diện P3 được dùng bổ sung và ghi riêng nguồn. Các hướng hành động dưới đây là đề xuất điều tra, không phải nguyên nhân đã xác nhận.

### 1. Tập trung vào vấn đề có khối lượng lớn, chưa có dấu hiệu bùng tăng ở kỳ cuối

Ba nhóm đứng đầu theo priority chứa 27.738/56.919 review được gán nhóm, khoảng 48,7%. Có 112 review tiêu cực mang nhãn chưa gán, nên mẫu số này khác tổng 57.031 review tiêu cực. Cả 12 nhóm đều có trend_status=stable ở kỳ 2012-10. Ưu tiên hiện tại chủ yếu phản ánh khối lượng và mức độ bất mãn, không chứng minh một cuộc khủng hoảng đang tăng nhanh. Nhãn nhóm còn rộng; không diễn giải 48,7% thành tỷ lệ của một nguyên nhân duy nhất.

Hành động đề xuất: Ưu tiên rà soát nhóm giao nhận, trải nghiệm mùi/vị và thông tin thành phần; chia nhỏ nguyên nhân trước khi giao nhiệm vụ cho từng bộ phận.

### 2. Độ kín bao bì là điểm kiểm tra cụ thể hơn việc quy toàn bộ lỗi cho vận chuyển

Nhóm bao bì có 5.302 phàn nàn. P4 tìm được review #402 mô tả 3/4 túi bung miệng dù không bị rách, và #567 mô tả túi mở, đồ ăn đổ trong hộp. Hai trường hợp chỉ ra việc cần kiểm tra đường hàn/miệng túi và cách đóng kiện, nhưng chưa xác định lỗi xảy ra tại nhà máy, kho hay trên đường giao.

Hành động đề xuất: Lấy mẫu kiểm tra độ kín trước xuất kho, đối chiếu ảnh kiện ngoài và bao bì trong; theo dõi tỷ lệ bung miệng túi theo SKU/lô thay vì chỉ theo hãng vận chuyển.

Nguồn: Review #402, Review #567

### 3. Sai lệch kỳ vọng xuất hiện ở cả thành phần, hương vị và hàng thực nhận

P4 #283 phản ánh tên gọi gợi kỳ vọng vị gạo nhưng thành phần/vị lại thiên về ngô. Review đại diện P3 #29075 phản ánh danh sách thành phần trên trang bán khác nhãn thực tế; #238663 phản ánh đặt một loại nhưng nhận loại khác. Đây là các cơ chế khác nhau cùng làm khách thấy sản phẩm không đúng kỳ vọng, cần tách lỗi thông tin khỏi lỗi lấy hàng.

Hành động đề xuất: Đối chiếu trang bán với nhãn sản phẩm theo phiên bản; kiểm tra mã biến thể lúc lấy hàng; không gom mọi phản hồi 'không như mong đợi' thành lỗi chất lượng.

Nguồn: Review #283, Review #29075, Review #238663

### 4. 'Không được trả hàng' có thể làm trải nghiệm xấu thêm, dù vẫn có phương án hoàn tiền

P4 #394 và các ví dụ P3 #360394, #312691 cho thấy khách hiểu rằng hàng thực phẩm không thể trả nên mình phải chịu thiệt. Trong khi đó #88512 kể đã được hoàn tiền sau hai lần nhận sai. Policy trong kho P4 cũng phân biệt không nhận hàng trả vật lý với hoàn tiền/đổi hàng không cần gửi lại. Bằng chứng gợi ý khoảng cách truyền thông hoặc xử lý hỗ trợ; chưa chứng minh toàn bộ khách bị từ chối hoàn tiền.

Hành động đề xuất: Làm rõ quy trình xử lý giao sai/hàng hỏng trên trang đơn hàng và kịch bản hỗ trợ; đo tỷ lệ liên hệ lại, thời gian xử lý và số lần khách phải giải thích lại.

Nguồn: Review #394, Review #360394, Review #312691, Review #88512, POL-RET-003::pol_POL-RET-003_2

### 5. Sản phẩm còn hạn vẫn có thể bị chê cũ/ôi; chưa đủ cơ sở quy về tồn kho hết hạn

P4 #542 và #619 mô tả cảm giác stale dù ngày hết hạn chưa qua. Các ví dụ P3 #119157 và #234066 lại phản ánh sản phẩm đã hết hạn khi nhận. Cần tách hai nhánh: giao hàng quá hạn và cảm quan không đạt khi còn hạn. Nguyên nhân của nhánh sau chưa được kiểm nghiệm.

Hành động đề xuất: Ghi đồng thời hạn sử dụng, mã lô, tình trạng niêm phong và mô tả cảm quan; kiểm tra lưu kho/bao bì bên cạnh quy tắc xuất hàng theo hạn.

Nguồn: Review #542, Review #619, Review #119157, Review #234066

### 6. Cần đọc nội dung: 5 sao không luôn đồng nghĩa với không có phàn nàn

P4 #899 cho 5 sao nhưng mô tả không chịu được mùi; #745 cũng cho 5 sao dù có nhận xét vị ôi/chua. Ngược lại #469 dùng 'weak at the knees' để khen khoai tây, khiến kết quả truy xuất cho nhóm 'weak' dễ lệch ngữ nghĩa. Review #371 xuất hiện ở hai chunk nhưng vẫn chỉ là một khách hàng, không phải hai bằng chứng độc lập.

Hành động đề xuất: Trong P5, đọc nguyên văn và phân biệt chunk với review; xem số sao là tín hiệu phụ. Đánh giá relevance trên một tập truy vấn có người duyệt trước khi dùng kết quả retrieval cho kết luận tự động.

Nguồn: Review #899, Review #745, Review #469, Review #371

### Giới hạn diễn giải

- Các insight do trợ lý đọc và tổng hợp, chưa có người đánh giá độc lập hoặc ground truth để chấm độ đúng.
- Các review trích dẫn là ví dụ; không suy ra tỷ lệ nguyên nhân bên trong một nhóm từ vài ví dụ truy xuất.
- Kho policy có hiệu lực năm 2026 trong khi review kết thúc năm 2012: chỉ dùng làm tham chiếu thiết kế quy trình, không kết luận khách hoặc bên bán đã vi phạm policy đó ở thời điểm lịch sử.
- Review là lời kể của khách; nguyên nhân ở nhà máy, kho hay vận chuyển cần dữ liệu vận hành để xác minh.
- Điểm ưu tiên là kết quả công thức P3, không phải dự báo doanh thu mất đi hoặc mức rủi ro đã kiểm định.

## #1 — ordered / item / received

- P3 assigned 9906 complaint reviews to this issue.
- 69.8% of assigned complaints are one-star reviews.
- P3 priority score: 67/100.
- This group accounts for 17.4% of complaints assigned by P3.
- P2 trend status in 2012-10: stable.
- P2 rolling-window share growth: +3.2% (separate from P3 growth).

### Giao nhận và xử lý sau mua là hai điểm cần tách để cải thiện nhóm ưu tiên cao nhất

P4 có trường hợp đơn không đến (#325), khách không biết cách xử lý sản phẩm không phù hợp vì không được trả (#394), và hàng bị khách mô tả là hỏng sau khi nhận (#775). Nội dung truy xuất của nhóm khá hỗn hợp. [Review #325, Review #394, Review #775]

Ví dụ P3 nêu giao sai biến thể (#238663, #360394), kể cả thay thế vẫn sai (#88512); đây là bằng chứng bổ sung từ P3, không phải kết quả P4 tìm trên toàn bộ kho. [Review #238663, Review #360394, Review #88512]

**Diễn giải:** Với 9.906 phàn nàn và 69,8% là 1 sao, đây là nơi nên bắt đầu điều tra. Tuy nhiên nhãn ordered/item/received đang gom nhiều loại sự cố; cần tách giao thiếu/giao sai khỏi tình trạng hàng và xử lý hỗ trợ.

**Chưa thể kết luận:** Chưa biết tỷ trọng từng lỗi con, mức thất thoát hay bên chịu trách nhiệm. Không thể coi toàn bộ 9.906 review là giao sai hàng.

**Hành động đề xuất:**

- Gắn nhãn lỗi con trên một mẫu review của nhóm để xác định nhánh chiếm nhiều phản hồi nhất.
- Đối chiếu mã biến thể đặt mua và mã quét khi lấy hàng; ghi nhận riêng trường hợp thay thế vẫn sai.
- Kiểm tra khách có được thông báo rõ phương án hoàn tiền/đổi hàng không cần trả vật lý hay không.


### Evidence

- [Review #325] (resolved, p4_output): Never Arrived. So we cancelled the order. It was cancelled without any problem. That is a positive note
- [Review #394] (resolved, p4_output): MSG Ham Base. I haven't used the ham base. It is loaded with MSG. I did not realize this when I ordered it and can not return it because it is a food item
- [Review #107] (resolved, p4_output): disappointing. not what I was expecting in terms of the company's reputation for excellent home delivery products
- [Review #775] (resolved, p4_output): Horrible .. dont buy it. The laddoos turned bad in a few days after we received it. No other item inside our fridge turned bad.
- [POL-RET-003::pol_POL-RET-003_3] (resolved, p4_output): [Customer Returns, Refunds, and Dispute Resolution Policy - 2. Damage & Quality Complaints Protocol]
## 2. Damage & Quality Complaints Protocol
- **Immediate Resolution SLA (POL-RET-002.1):** Customers reporting transit damage (leaking bottle, broken glass, crushed box) within 30 days of receipt are eligible for:
  1. Full refund to original payment method or instant store credit.
  2. Free 1-business-day expedited replacement shipment.
- **Photo Evidence Requirement:** For orders under $50, no photo proof is required for the first 2 complaint occurrences per customer account. For orders exceeding $50 or recurring claims, an image of the shipping label and damaged item is requested for courier claims.
- [POL-RET-003::pol_POL-RET-003_2] (resolved, p4_output): [Customer Returns, Refunds, and Dispute Resolution Policy - 1. Non-Returnable Perishable & Food Items]
## 1. Non-Returnable Perishable & Food Items
- **Health & Safety Prohibition (POL-RET-001.1):** For hygiene and food safety reasons, opened or unopened grocery and food products cannot be physically returned to fulfillment centers.
- **"Returnless Refund" Guarantee (POL-RET-001.2):** When a customer reports spoiled, damaged, stale, or incorrect food items, customer service representatives are authorized to issue an instant full refund or replacement without requesting return shipment.
- [Review #238663] (resolved, p3_example): Wrong item. I ordered fruit and nut gronila but received three berry instead. Unfortunately I had it sent to a friend who was unaware of the mistake and was unable to return by the time I got the item.
- [Review #360394] (resolved, p3_example): wrong product sent. It is hard to review this product we ordered Black Peppercorn marinade and received white wine marinade! If you can get Black Peppercorn it is a great product! With that being said there is a no return on this item so if they send you the wrong marinade you are stuck with 12 packages of it!
- [Review #88512] (resolved, p3_example): Received wrong item twice. I ordered this item once and received the sugar free version. Then on the replacement order Amazon sent, it was still the wrong product. However, customer service was great and they refunded me within 48 hours.


## #2 — away / smell / gave

- P3 assigned 10580 complaint reviews to this issue.
- 60.4% of assigned complaints are one-star reviews.
- P3 priority score: 57.6/100.
- This group accounts for 18.6% of complaints assigned by P3.
- P2 trend status in 2012-10: stable.
- P2 rolling-window share growth: +0.9% (separate from P3 growth).

### Mùi và cảm quan không chấp nhận được tạo ra hành vi bỏ sản phẩm, nhưng số sao có thể che khuất phản hồi

P4 #899 và #745 có nội dung chê mùi/vị dù cho 5 sao. Vì thế các review này có thông tin phàn nàn thực sự, không nên loại chỉ vì rating cao. [Review #899, Review #745]

Ví dụ P3 #528009, #103436 và #537738 kể việc dừng sử dụng hoặc vứt bỏ sản phẩm vì kết cấu/mùi không chấp nhận được. [Review #528009, Review #103436, Review #537738]

**Diễn giải:** Nhóm lớn nhất theo số lượng có 10.580 phàn nàn, nhưng từ khóa away/smell/gave chưa tạo thành một loại lỗi đồng nhất. Hành vi bỏ sản phẩm là tín hiệu bất mãn hữu ích để đọc sâu; không phải bằng chứng xác nhận sản phẩm hỏng.

**Chưa thể kết luận:** Chưa phân biệt được đặc trưng mùi tự nhiên, sở thích cá nhân và suy giảm chất lượng; chưa có kiểm nghiệm hay thông tin lô.

**Hành động đề xuất:**

- Tách mô tả mùi khỏi kết cấu và hành vi vứt bỏ để giảm độ rộng của nhóm.
- Đọc nội dung cả review rating cao khi rà soát mùi/vị.
- Thu thập mã lô và điều kiện bảo quản cho các phản hồi cảm quan tương tự trước khi gán nguyên nhân.


### Evidence

- [Review #899] (resolved, p4_output): I can't take the smell. The product is all that it says it is which is why I gave it 5 stars. However, I do have issues with the product, namely, me and my family members can't take the smell. The taste is horrible so I put it in a lotion cream and rubbed it on my skin. This was a few weeks ago and though I've since changed my sheets, the scent is still in my bed. Ultimately, I stopped using it because it made me smell in a way I did not like. It smells like an Indian spice and while it didn't work for me, scent-wise, it may work fine with someone else.
- [Review #817] (resolved, p4_output): obsessively chewing this product I filled my gut with odorless room air and so helped me lose 25# in 3 months. Also, it doesn't lose its flavor on the bedpost overnight.
- [Review #974] (resolved, p4_output): deal?? 12 x 19 = 228 singles so $69 / 228 = .302 per single - the most expensive at all.
- [Review #745] (resolved, p4_output): it gave everything a slightly rancid, soury taste...no idea why! Due to the higher calories and higher price, I will only stock this as emergency food. I will buy more for that reason.
- [POL-RET-003::pol_POL-RET-003_2] (resolved, p4_output): [Customer Returns, Refunds, and Dispute Resolution Policy - 1. Non-Returnable Perishable & Food Items]
## 1. Non-Returnable Perishable & Food Items
- **Health & Safety Prohibition (POL-RET-001.1):** For hygiene and food safety reasons, opened or unopened grocery and food products cannot be physically returned to fulfillment centers.
- **"Returnless Refund" Guarantee (POL-RET-001.2):** When a customer reports spoiled, damaged, stale, or incorrect food items, customer service representatives are authorized to issue an instant full refund or replacement without requesting return shipment.
- [POL-FQD-002::pol_POL-FQD-002_3] (resolved, p4_output): [Food Quality, Freshness, and Shelf Life Standards - 2. Sensory & Freshness Integrity]
## 2. Sensory & Freshness Integrity
- **Stale, Rancid, or Off-Flavor Defect (POL-FQD-002.1):** Nuts, oils, whole-grain snacks, and roasted coffee displaying oxidation, bitterness, rancid odors, or stale texture prior to the printed expiration date indicate barrier failure, seal compromise, or warehouse storage above 75°F.
- **Foreign Matter & Contamination (POL-FQD-002.2):** Reports of mold, insects, foreign particles, or discoloration require an immediate batch freeze and notification of the supplier QA lead within 24 hours.
- [Review #528009] (resolved, p3_example): I couldn't even finish eating 1.... I don't know what the others who gave this a good review ate but it is not what I got! I tried these and I couldn't even finish the one I was eating. I took 1 bite and threw the rest away. As did my husband. I then threw the whole bag away. They were grainy, dry, and not chocolaty at all. Seriously gross.
- [Review #103436] (resolved, p3_example): Worse than Bad!. I was excited to get a healthy protein treat and I was hugely disappointed. I opened the first one and was appalled by the smell. I managed to choke down three bites and the only good thing I can say about this stuff is that it didn't make me sick immediately. I threw the rest away. Later I went back in the kitchen and thought I smelled where my little dog had an accident but it was only the open package reeking from the trash. I have eaten homemade ostrich jerky but this tastes nothing like it. It is hard to believe it is ostrich. Do not buy this product. Even my cats and dog couldn't eat it.
- [Review #537738] (resolved, p3_example): Worst Smell. I was very disappointed with this product. The description says thick and compares it to 3 pencils. The bully sticks I got were only about one pencil thick. Their smell was so awful that I took it away from my dog after 10 minutes. You can only return things for store credit and I do not want anything else from this seller. I threw the rest away.

> Retrieved evidence includes 4–5-star reviews; inspect text rather than inferring sentiment from rating alone.

## #3 — ingredients / ingredient / list

- P3 assigned 7252 complaint reviews to this issue.
- 66.2% of assigned complaints are one-star reviews.
- P3 priority score: 55/100.
- This group accounts for 12.7% of complaints assigned by P3.
- P2 trend status in 2012-10: stable.
- P2 rolling-window share growth: -7.8% (separate from P3 growth).

### Minh bạch thành phần là vấn đề về độ khớp thông tin, không chỉ về khẩu vị

P4 #283 cho thấy kỳ vọng về thành phần/vị dựa vào tên sản phẩm không trùng với trải nghiệm sau khi đọc nhãn và dùng thử. [Review #283]

P3 #29075 và #186600 phản ánh thành phần trên trang bán khác nhãn nhận được; policy P4 có mục Product Formulation & Label Accuracy để tham chiếu khi thiết kế bước đối chiếu. [Review #29075, Review #186600, POL-FQD-002::pol_POL-FQD-002_4]

**Diễn giải:** Nhóm có 7.252 phàn nàn, 66,2% là 1 sao. Hướng xử lý có cơ sở là kiểm tra tính nhất quán giữa tên sản phẩm, thông tin trang bán và nhãn theo phiên bản, thay vì chỉ giải thích rằng khách không thích vị.

**Chưa thể kết luận:** Các lời kể chưa chứng minh mọi listing đều sai; chưa xác minh phiên bản công thức tại thời điểm mua hoặc kết luận về ảnh hưởng sức khỏe của thành phần.

**Hành động đề xuất:**

- Đối chiếu listing, ảnh nhãn và dữ liệu thành phần theo từng SKU/phiên bản.
- Lưu ngày cập nhật công thức và thông báo thay đổi cho người mua lại.
- Phân biệt phản hồi 'không thích thành phần' với 'thành phần không khớp mô tả' khi phân loại.


### Evidence

- [Review #540] (resolved, p4_output): honey powder, onion and sugar), to take the edge of the stonger flavours (paprika, chili pepper, cayenne pepper, and natural smoke flavour), of which there is less, (they come further down in the list of ingredients than the sweeteners.) The complete list of ingredients of these KETTLE BACKYARD BARBECUE CHIPS, (in the 1-ounce bags, and hopefully, in the 9 ounce bags as well), is as follows: Potatoes Vegetable Oil, (Safflower and Sunflower Oil), Honey Powder, (Dried cane sugar, honey), Rice Powder Sugar Salt Onion Powder Tomato Powder Paprika Torula Yeast Garlic Powder Chili Pepper Citric Acid Cayenne Pepper Paprika Oleoresin, (Colour) Natural Smoke Flavour Naturally cooked, natural ingredients. The combination is a true taste treat! Of course, as with all
- [Review #283] (resolved, p4_output): Over priced chips and lack rice taste. I paid $1.79 for a 2 ounce pkg of these at lunch today. I bought them because brown rice is a "good" carb. As soon as I tasted one and it tasted like a corn chip I checked the ingredients. The name is deceptive - these have "Masa corn flour" listed in the ingredients and it overwhelms the taste. I won't buy these again - I can get Sunchips for less money and similar taste.
- [Review #408] (resolved, p4_output): Ingredients take about 2 seconds to read. This is a simple product and it is simply good. There are no extra ingredients that are hard to pronounce and have you scouring the internet finding out what they are. It is a bit thinner consistency than the usual syrup, so use caution the first time you go to squeeze some out. This will be great for people who like mint, it has a much stronger mint flavor than chocolate. I use it in my coffee with a bit of half and half, tastes great. Sometimes simple is better.
- [Review #746] (resolved, p4_output): call it juice but it's as thick as an Odwalla drink like a smoothie. With all that's in it, this is a very good value. Considering you can pay as much for any one of the ingredients in it. My personal use is to add this to kombucha, maximizing it's longevity that way, I've tried many but this one is the best for kombucha. They say an 8oz glass has 2 servings of fruit on the Lakewood website. It's quite tasty in that it's not too sweet, very thick textured even with the tiny bits of seed in it reminiscent of a banana smoothie. The ingredient list is somewhat confusing but note that only the Acerola Cherry is from concentrate,
- [POL-FQD-002::pol_POL-FQD-002_4] (resolved, p4_output): [Food Quality, Freshness, and Shelf Life Standards - 3. Product Formulation & Label Accuracy]
## 3. Product Formulation & Label Accuracy
- **Ingredient & Allergen Transparency (POL-FQD-003.1):** When a brand updates formulation (e.g., changes sweetener, alters sodium, or changes allergen facilities), packaging must feature a prominent "New Recipe" callout on the front label for a minimum of 6 months.
- **Organic & Non-GMO Integrity:** Certified organic products must be stored separated from non-organic goods in accordance with USDA National Organic Program standards.
- [POL-FQD-002::pol_POL-FQD-002_1] (resolved, p4_output): [Food Quality, Freshness, and Shelf Life Standards - Food Quality, Freshness, and Shelf Life Standards]
# Food Quality, Freshness, and Shelf Life Standards

**Document ID:** POL-FQD-002
**Category:** Quality Assurance & Safety
**Effective Date:** 2026-01-01
- [Review #29075] (resolved, p3_example): Contains MSG. I relied on the ingredients listed on Amazon's site. Ingredients Peanuts, Dry Roast Seasoning, Tapioca Dextrin, Natural Flavoring, Salt. Guess what? When the product arrived I read the laundry list of about 20 other ingredients. According to the actual label the Dry Roast "seasoning" contains MSG. Now I'm not that paranoid about MSG but if the product has it as an ingredient it should have been listed on Amazon. I wish they had shown the nutrition label. It also contains added sugar. What's wrong with plain dry roasted peanuts? The taste is about what you would expect. Peanuts with a flavor coating. I will not buy them again. Also it is a 12 pack.
- [Review #97527] (resolved, p3_example): Warning, Contains High Fructose Corn Syrup. This was my favorite cereal for years...until I read the label. I guess I took for granted the ingredients because of the commercials and advertising of it as such a healthy cereal and even promoted it as a diet plan to lose weight. I hope the manufacturers realize how many people discontinued purchasing this great product after educating themselves on the dangers of high fructose corn syrup. They need to reconfigure their ingredients list to actually make something that won't be eventually blacklisted for being harmful to unsuspecting consumers.
- [Review #186600] (resolved, p3_example): Contains Corn Syrup despite Website Ingredients Stating otherwise. Not happy that I decided to try this formula because it did not contain added sugar (per ingredient listing on the company's website). When I received it, the ingredient list listed "corn syrup" (i.e., SUGAR). I wrote to the company and asked about it and their response was "the amount of carbohydrates is the same" and that it was an "improved formula". Its unfortunate that you can't even trust a seemingly small, organic company to be forthcoming about ingredients that are unhealthy for infants!

> Retrieved evidence includes 4–5-star reviews; inspect text rather than inferring sentiment from rating alone.

## #4 — money / waste / waste money

- P3 assigned 3843 complaint reviews to this issue.
- 79.9% of assigned complaints are one-star reviews.
- P3 priority score: 40.4/100.
- This group accounts for 6.8% of complaints assigned by P3.
- P2 trend status in 2012-10: stable.
- P2 rolling-window share growth: +5.4% (separate from P3 growth).

### 'Lãng phí tiền' mô tả kết quả bất mãn, chưa chỉ ra một lỗi vận hành duy nhất

P4 #556 cho biết khách bỏ cả hai thùng snack nhưng không mô tả đủ nguyên nhân; nhiều kết quả khác trong nhóm lại mang tính khen giá trị. [Review #556, Review #743, Review #665]

P3 có ví dụ về lượng hàng không xứng giá (#340642), đồ chơi không tạo thời gian sử dụng như mong đợi (#158936), và sản phẩm không đạt công dụng kỳ vọng (#343413). [Review #340642, Review #158936, Review #343413]

**Diễn giải:** Dù 79,9% trong 3.843 phàn nàn là 1 sao, không nên kết luận nguyên nhân chính là giá cao. Nhóm này biểu đạt mức thất vọng mạnh và cần được gán thêm nhãn nguyên nhân.

**Chưa thể kết luận:** Chưa biết tỷ lệ do giá, quy cách, công dụng hay chất lượng; không suy ra mức thiệt hại tài chính từ số review.

**Hành động đề xuất:**

- Phân loại lại theo nguyên nhân cụ thể trước khi đề xuất giảm giá hoặc khuyến mại.
- Đối chiếu số lượng/quy cách và mô tả công dụng với kỳ vọng người mua.
- Theo dõi lý do hoàn tiền của nhóm này thay vì chỉ đếm cụm từ waste money.


### Evidence

- [Review #743] (resolved, p4_output): Dum Dums for all!!. I work in college Financial Aid and keep a bowl of these on my desk for the students. I used to buy them in the grocery store then learned I could get them for less online ($17 for 3lb bag) and thought that was a good deal - until I found this GREAT deal!
- [Review #556] (resolved, p4_output): Garbage. Don't waste your money on any of the Kettle brand potato chips. I bought a case of these, and a case of the cheddar and sour cream. Both cases ended up in the garbage can.
- [Review #947] (resolved, p4_output): You just rinse it and put it in a different bin and still put it out on trash day. Stop being lazy.
- [Review #665] (resolved, p4_output): do purchase this sweetner, take advantage of ship and save, it will save you lots of money in the long run.
- [POL-RET-003::pol_POL-RET-003_2] (resolved, p4_output): [Customer Returns, Refunds, and Dispute Resolution Policy - 1. Non-Returnable Perishable & Food Items]
## 1. Non-Returnable Perishable & Food Items
- **Health & Safety Prohibition (POL-RET-001.1):** For hygiene and food safety reasons, opened or unopened grocery and food products cannot be physically returned to fulfillment centers.
- **"Returnless Refund" Guarantee (POL-RET-001.2):** When a customer reports spoiled, damaged, stale, or incorrect food items, customer service representatives are authorized to issue an instant full refund or replacement without requesting return shipment.
- [POL-RET-003::pol_POL-RET-003_1] (resolved, p4_output): [Customer Returns, Refunds, and Dispute Resolution Policy - Customer Returns, Refunds, and Dispute Resolution Policy]
# Customer Returns, Refunds, and Dispute Resolution Policy

**Document ID:** POL-RET-003
**Category:** Customer Support & Operations
**Effective Date:** 2026-01-01
- [Review #340642] (resolved, p3_example): Waste of money!! Do not buy this!. This was the total waste of money and time to buy this product. Probably the worst product I bought from Amazon. They three 'small' packs of herseys. Even at the corner shops, you can get better deals, don't waste your money on this deal.
- [Review #158936] (resolved, p3_example): Total Waste of Money. I was so looking forward to hours of enjoyment for my basset hounds but it turned out they figured out how to get the treats out in less than 5 minutes. What fun is that for them or for me? I'll go broke reloading treats all the time. Don't waste your money. Medium difficulty?? I don't think so. I invested close to $40 and I doubt I can return it because it is full of basset slobber now.
- [Review #343413] (resolved, p3_example): Do not waste your money. I bought 3 of the Flea Traps, and 3 packs of the refills. Total waste of money. Fleas are jumping on me but yet none in the traps. So if you want a product to get rid of Fleas don't buy this one.

> Retrieved evidence includes 4–5-star reviews; inspect text rather than inferring sentiment from rating alone.

## #5 — box / boxes / packaging

- P3 assigned 5302 complaint reviews to this issue.
- 62.3% of assigned complaints are one-star reviews.
- P3 priority score: 35.8/100.
- This group accounts for 9.3% of complaints assigned by P3.
- P2 trend status in 2012-10: stable.
- P2 rolling-window share growth: +3.6% (separate from P3 growth).

### Bung miệng túi và thiếu bao bì trong là các lỗi có thể kiểm tra trực tiếp

P4 #402 mô tả 3/4 túi bung ở miệng, không rách; #567 mô tả nhiều túi mở và đồ ăn tràn trong kiện. Đây là tín hiệu để kiểm tra độ kín và đóng gói. [Review #402, Review #567]

Ví dụ P3 #312691 và #30701 bổ sung tình huống túi hở hoặc sản phẩm không có túi/hộp trong như mô tả. Policy P4 có quy trình xử lý khiếu nại hàng hỏng để tham chiếu. [Review #312691, Review #30701, POL-RET-003::pol_POL-RET-003_3]

**Diễn giải:** Trong 5.302 phàn nàn, các ví dụ trên cho hướng điều tra cụ thể hơn nhãn chung 'vận chuyển kém': kiểm tra đường hàn/miệng túi, sự hiện diện của bao bì trong và cấu trúc đóng kiện.

**Chưa thể kết luận:** Không thể xác định thời điểm bung túi hoặc quy trách nhiệm cho đơn vị vận chuyển chỉ từ lời kể; nhóm cũng có phản hồi về kích thước bao bì thay vì hư hỏng.

**Hành động đề xuất:**

- Ghi nhận riêng bung đường hàn, rách do va chạm, thiếu bao bì trong và quy cách gây hiểu nhầm.
- Lấy mẫu kiểm tra niêm phong trước xuất kho và đối chiếu ảnh kiện khi nhận.
- Theo dõi tỷ lệ lỗi theo SKU/lô/kiểu bao bì để khoanh vùng thử nghiệm cải tiến.


### Evidence

- [Review #567] (resolved, p4_output): HORRIBLE I CANT BELIEVE THIS!. Terrible! I cannot believe this, I received this item and EVERY SINGLE BAG WAS OPENED BUT 4!!! I'm stationed in Afghanistan and this was gonna be a snack for my team while going out on missions. I was so embarrassed when the bags were opened and spilt out all in the box, gross! And the box is filled with grease stains. Idk if it was from the airplane ride all the way here, but the box should have been more insulated and bubble wrap should have been used instead of paper. I'm very unhappy with stale crusty chips out the bag and us soldiers cannot enjoy now.
- [Review #402] (resolved, p4_output): poor item packaging. This mix is very poorly packaged and breaks open easily during shipping. Nearly a full bag of my order was spilled in the shipping box. 3 bags out of 4 had come unsealed at the top. There were no tears in the packages.
- [Review #873] (resolved, p4_output): Really wanted to like these.... This product must qualify for some sort of deceptive packaging award. The box only contains 5 bars and the wrappers are smaller than normal, so at least 50% of the interior of the box is air. Then when you unwrap the bar you find they are only about 60% the length of a "normal" snack bar. The rest of it is empty air inside the wrapper. If they were to not include wrappers those 5 bars would occupy less than 25% of the space inside the box. As far as taste goes they are so-so. On the dry side with a hint of berry flavor. Celiacs, who are used to inferior products, won't be disappointed
- [Review #329] (resolved, p4_output): inner boxes. Thus, none of my cups were broken, no waste and no sloppy drippy mess. Plus the four boxes means I could put one in the kitchen, one in the bathroom (we moved our mini Keurig there when we upgraded the kitchen Keurig - best idea my husband ever had), and one at work, with a reserve for whichever runs out first. If you are looking for these mini creamers but deterred like I was by the negative packaging reviews on other options, this is your best bet. As a bonus, the auto delivery price is very reasonable.
- [POL-RET-003::pol_POL-RET-003_3] (resolved, p4_output): [Customer Returns, Refunds, and Dispute Resolution Policy - 2. Damage & Quality Complaints Protocol]
## 2. Damage & Quality Complaints Protocol
- **Immediate Resolution SLA (POL-RET-002.1):** Customers reporting transit damage (leaking bottle, broken glass, crushed box) within 30 days of receipt are eligible for:
  1. Full refund to original payment method or instant store credit.
  2. Free 1-business-day expedited replacement shipment.
- **Photo Evidence Requirement:** For orders under $50, no photo proof is required for the first 2 complaint occurrences per customer account. For orders exceeding $50 or recurring claims, an image of the shipping label and damaged item is requested for courier claims.
- [POL-RET-003::pol_POL-RET-003_2] (resolved, p4_output): [Customer Returns, Refunds, and Dispute Resolution Policy - 1. Non-Returnable Perishable & Food Items]
## 1. Non-Returnable Perishable & Food Items
- **Health & Safety Prohibition (POL-RET-001.1):** For hygiene and food safety reasons, opened or unopened grocery and food products cannot be physically returned to fulfillment centers.
- **"Returnless Refund" Guarantee (POL-RET-001.2):** When a customer reports spoiled, damaged, stale, or incorrect food items, customer service representatives are authorized to issue an instant full refund or replacement without requesting return shipment.
- [Review #312691] (resolved, p3_example): Waste of my money. I was so excited when I ordered this product and received it today. When I put the box on my counter I notice powder spilling out of the packaging box. I opened up the box and the bag had popped open about half an inch at the top and about a cup of powder had spilled inside the box. I don't know whether it had burst open or been open but I personally don't trust an open food package when I buy it. I can't even return the product because of it's "no return" return policy. Waste of my $25 and extremely disappointed...stick with starbucks and don't let what happened to me happen to you.
- [Review #442061] (resolved, p3_example): WHAT A DISASTER!. I should have believed the other reviewers! When I opened the box the bag that the chocolate was in was torn open and the chocolate coins were scattered all over the box! I was very disappointed! This was a gift and there was no way that I could give this to anyone! There is no way that the outer bag ripped inside the sealed box. This ccompany needs to check out what is going on with who is packing the boxes that are being shipped out!
- [Review #30701] (resolved, p3_example): Terrible Packaging. We opened the box to find the jelly beans sitting directly in the box. No bag, no plastic container (as the description states)...just literally a cardboard box full of jelly beans. How clean are cardboard shipping boxes? The box was taped on top to seal it but air, bugs could easily get through the unsealed edges. The jelly beans were good and still tasted fresh but we were very disappointed in the packaging.

> Retrieved evidence includes 4–5-star reviews; inspect text rather than inferring sentiment from rating alone.

## #6 — old / formula / changed

- P3 assigned 3376 complaint reviews to this issue.
- 65.2% of assigned complaints are one-star reviews.
- P3 priority score: 27.8/100.
- This group accounts for 5.9% of complaints assigned by P3.
- P2 trend status in 2012-10: stable.
- P2 rolling-window share growth: +5.1% (separate from P3 growth).

### Thay đổi công thức có thể làm mất kỳ vọng của người mua lại; P4 hiện hỗ trợ chủ đề này còn yếu

Review đại diện P3 #120030 phản ánh công thức/bao bì thay đổi trong khi trang bán vẫn dùng hình cũ; #432056 nói khách đang tìm sản phẩm thay thế vì không thích công thức mới. [Review #120030, Review #432056]

P4 tìm được các mục về cảm quan và thay đổi công thức, nhưng review #63 nói về stale và #124 nói về lựa chọn thức ăn cho mèo; các đoạn này chưa trực tiếp chứng minh lỗi đổi công thức trong nhóm. [Review #63, Review #124, POL-FQD-002::pol_POL-FQD-002_4]

**Diễn giải:** Hướng hành động hợp lý cho nhóm 3.376 phàn nàn là minh bạch phiên bản công thức và đối chiếu nội dung bán hàng. Kết luận này dựa chủ yếu vào ví dụ P3 bổ sung, không nên trình bày như thành quả truy xuất mạnh của P4.

**Chưa thể kết luận:** Chưa có lịch sử công thức hoặc dữ liệu mua lại để xác nhận mức rời bỏ; không thể coi mọi từ old là chỉ công thức cũ.

**Hành động đề xuất:**

- Gắn phiên bản công thức với ảnh và mô tả listing.
- Tách 'old formula' khỏi 'old/stale product' khi đọc nhóm.
- Nếu có dữ liệu vận hành, so sánh mua lại và lý do hoàn tiền trước/sau lần thay đổi.


### Evidence

- [Review #63] (resolved, p4_output): stale product.. Arrived in 6 days and were so stale i could not eat any of the 6 bags!!
- [Review #124] (resolved, p4_output): Palatable and healthy. Before I was educated about feline nutrition, I allowed my cats to become addicted to dry cat food. I always offered both canned and dry, but wish I would have fed them premium quality canned food and limited dry food. I have two 15 year old cats and two 5 year old cats. The only good quality dry foods they will eat are Wellness and Innova. Innova's manufacturer was recently purchased by Procter&Gamble. I began looking for a replacement. After once again offering several samples (from my local holistic pet store) Holistic Select was the only one (other than the usual Wellness and Innova) they would eat. For finicky cats, I recommend trying Holistic Select. It is
- [Review #619] (resolved, p4_output): I dont know if.... I dont know if they were fresh or if they were supposed to taste like they did. I checked the expiration date it was current but still tasted kind of stale to me !!!
- [Review #262] (resolved, p4_output): YUMMY. A great healthy chew for my 9 wk old beagle, Rio. He loves the taste and it sure beats my arm.
- [POL-FQD-002::pol_POL-FQD-002_3] (resolved, p4_output): [Food Quality, Freshness, and Shelf Life Standards - 2. Sensory & Freshness Integrity]
## 2. Sensory & Freshness Integrity
- **Stale, Rancid, or Off-Flavor Defect (POL-FQD-002.1):** Nuts, oils, whole-grain snacks, and roasted coffee displaying oxidation, bitterness, rancid odors, or stale texture prior to the printed expiration date indicate barrier failure, seal compromise, or warehouse storage above 75°F.
- **Foreign Matter & Contamination (POL-FQD-002.2):** Reports of mold, insects, foreign particles, or discoloration require an immediate batch freeze and notification of the supplier QA lead within 24 hours.
- [POL-FQD-002::pol_POL-FQD-002_4] (resolved, p4_output): [Food Quality, Freshness, and Shelf Life Standards - 3. Product Formulation & Label Accuracy]
## 3. Product Formulation & Label Accuracy
- **Ingredient & Allergen Transparency (POL-FQD-003.1):** When a brand updates formulation (e.g., changes sweetener, alters sodium, or changes allergen facilities), packaging must feature a prominent "New Recipe" callout on the front label for a minimum of 6 months.
- **Organic & Non-GMO Integrity:** Certified organic products must be stored separated from non-organic goods in accordance with USDA National Organic Program standards.
- [Review #169411] (resolved, p3_example): Back to the old chocolate twizzlers. Several years ago, when they first changed the chocolate twizzlers I wrote to the company to complain also. Last week in the mail, I received a letter with coupons. The letter said they are going back to the old formula since so many people complained. Sounded to me like they will have both the old and new formula. They told me to look for the bag that says "Now in the Classic Twist". Can't wait to try them again!
- [Review #120030] (resolved, p3_example): Not what it used to be. The Cereal has changed. The company Attune foods which bought the old company has changed the recipe. It is no longer in the purplish box that Amazon shows, it is in a golden box and the cereal is now called Honey rice twice. The new recipe does not taste like the old rice twice, the new cereal is very sweet and has a fake taste like a child's cereal. So be aware If you are like me and loved the original rice twice you cannot get it anymore. Amazon should not be showing the old product box.
- [Review #432056] (resolved, p3_example): Such a shame they changed the formula!!!. I was such a fan of the old formula and would stock up and buy boxes at a time. I have a heavy work and travel schedule and this was the perfect bar for eating "healthy on the go." Now the calorie and fat content is much higher and the taste has changed for the worse! I wish the company would go back to the original formula...I am on the hunt for another bar! Such a shame...it was the best bar on the market!

> Retrieved evidence includes 4–5-star reviews; inspect text rather than inferring sentiment from rating alone.

## #7 — tasted / tasted like / tastes like

- P3 assigned 3418 complaint reviews to this issue.
- 65.8% of assigned complaints are one-star reviews.
- P3 priority score: 25.1/100.
- This group accounts for 6.0% of complaints assigned by P3.
- P2 trend status in 2012-10: stable.
- P2 rolling-window share growth: -1.6% (separate from P3 growth).

### Không thích vị và nghi ngờ sản phẩm cũ đang bị gộp trong cùng nhóm cảm quan

P4 #335 nghi ngờ cà phê stale, #27 chê kẹo không có vị; #650 lại cho thấy cách sử dụng/phối trộn làm thay đổi trải nghiệm vị. [Review #335, Review #27, Review #650]

P3 #415700 chê vị nhạt như bìa giấy, trong khi #52842 mô tả cả mùi và vị khó chịu. [Review #415700, Review #52842]

**Diễn giải:** Nhóm 3.418 phàn nàn là một tập vấn đề cảm quan, chưa phải một căn nguyên. Nên tách mức độ đậm vị, kỳ vọng hương vị, cách dùng và dấu hiệu bất thường.

**Chưa thể kết luận:** Chưa biết tỷ lệ từng nhánh và chưa kiểm nghiệm tình trạng stale; sự khác nhau về sở thích có thể giải thích một phần phản hồi.

**Hành động đề xuất:**

- Mã hóa lại phản hồi theo vị nhạt, vị lạ, mùi bất thường và cách dùng.
- Kiểm tra tính rõ ràng của hướng dẫn sử dụng khi khách cần pha/trộn sản phẩm.
- Chỉ chuyển sang điều tra chất lượng theo lô khi có bằng chứng phù hợp, không dựa riêng vào từ taste.


### Evidence

- [Review #335] (resolved, p4_output): Does not taste very good. Taste like it is stale. Will not order this again. I had this coffee at a 50th year annerversery at a reception hall and had to have it. This stuff tasted NOTHING, like the Douwe Egberts at the hall. This is possibly stale coffee.
- [Review #27] (resolved, p4_output): Nasty No flavor. The candy is just red , No flavor . Just plan and chewy . I would never buy them again
- [Review #650] (resolved, p4_output): Do not taste from bottle! Mix with vanilla for true flavor.. So I got this and tasted it strait out of the bottle, it tasted like smoky flavored milk - YUCK! I was depressed I was stuck with 4 bottles of this. It sat on my shelf and I forgot about it. Last weekend I tasted a Zevia cream soda and was not pleased with the flavor, it tasted weird and smokey like the LorAnn oil I had gotten. I tried to doctor up the soda with a little SF Vanilla Torani syrup and a tablespoon of heavy cream - IT TASTED AMAZING!!! The odd smokiness was gone and it had a wonderful rich mouthfeel. So I wanted to see
- [Review #963] (resolved, p4_output): The most awful taste. I purchased this because I read that it was a natural cure for hives..Um, how about NOT. It did nothing for my hives and it tastes awful. Luckily, a co-worker of mine loves this stuff (reminds him of his grandmother) and I gave it to him. Yucky, yucky stuff.
- [POL-RET-003::pol_POL-RET-003_4] (resolved, p4_output): [Customer Returns, Refunds, and Dispute Resolution Policy - 3. Product Reformulation / Dislike Discontent]
## 3. Product Reformulation / Dislike Discontent
- **Taste Satisfaction Guarantee (POL-RET-003.1):** If a customer dislikes the flavor, texture, or finds a recipe change unsatisfactory within 14 days, support grants a one-time courtesy credit equal to the product value.
- **Recurring Issue Escalation:** When 5 or more distinct customers complain about the same batch code for off-taste or early spoilage within a 7-day window, the SKU must be automatically paused from new order dispatch pending merchant review.
- [POL-FQD-002::pol_POL-FQD-002_3] (resolved, p4_output): [Food Quality, Freshness, and Shelf Life Standards - 2. Sensory & Freshness Integrity]
## 2. Sensory & Freshness Integrity
- **Stale, Rancid, or Off-Flavor Defect (POL-FQD-002.1):** Nuts, oils, whole-grain snacks, and roasted coffee displaying oxidation, bitterness, rancid odors, or stale texture prior to the printed expiration date indicate barrier failure, seal compromise, or warehouse storage above 75°F.
- **Foreign Matter & Contamination (POL-FQD-002.2):** Reports of mold, insects, foreign particles, or discoloration require an immediate batch freeze and notification of the supplier QA lead within 24 hours.
- [Review #10285] (resolved, p3_example): They taste sooo bad!!! Gross!!!. I got these for my dad from his wish list. He thought they would be spicy and flavorful but they just tasted like cumin and had a funky smell. The box came with 18 individual bags but after you open one bag, it's impossible to even want to put yourself through that again. They are nasty!!! Avoid them at all cost!! Yuck!!
- [Review #415700] (resolved, p3_example): Tastes like cardboard, yuck!!. I bought this product based on all the 5 star reviews. I really wanted to like it. First I had it with cold milk. Yuck, it tasted like cardboard. Then I tried it warmed up like oatmeal & added brown sugar. Still tastes like cardboard. How can anything so tasteless be loved by so many people?
- [Review #52842] (resolved, p3_example): Rank, Gross and Disgusting . . .. I have eaten Smoked Salmon for sixty years, I love it, but the stink of this stuff was enough to turn your stomach. And, if possible the second package was worse than the first. Both tasted as bad as they smelled . . .

> Retrieved evidence includes 4–5-star reviews; inspect text rather than inferring sentiment from rating alone.

## #8 — date / stale / expiration

- P3 assigned 2072 complaint reviews to this issue.
- 67.9% of assigned complaints are one-star reviews.
- P3 priority score: 21.8/100.
- This group accounts for 3.6% of complaints assigned by P3.
- P2 trend status in 2012-10: stable.
- P2 rolling-window share growth: +6.2% (separate from P3 growth).

### Cần tách hàng quá hạn khỏi hàng còn hạn nhưng cảm quan kém

P4 #542 và #619 đều mô tả cảm giác stale khi hạn sử dụng chưa qua. Điều này cho thấy chỉ kiểm tra ngày in trên nhãn chưa giải thích hết phản hồi. [Review #542, Review #619]

P3 #119157 và #234066 phản ánh hàng đã quá hạn khi nhận. P4 có hai mục riêng về hạn dùng và cảm quan để tham chiếu cho hai nhánh kiểm tra. [Review #119157, Review #234066, POL-FQD-002::pol_POL-FQD-002_2, POL-FQD-002::pol_POL-FQD-002_3]

**Diễn giải:** Với 2.072 phàn nàn và 67,9% là 1 sao, nhóm này có tiêu chí thu thập bằng chứng rõ: ngày đặt/nhận, hạn dùng, lô và tình trạng bao bì. Hai nhánh cần cách điều tra khác nhau.

**Chưa thể kết luận:** Không thể quy mọi trường hợp stale cho hàng hết hạn, bảo quản sai hoặc niêm phong lỗi nếu chưa có ảnh/lô và kiểm tra thực tế.

**Hành động đề xuất:**

- Đối chiếu hạn dùng ở khâu nhập và xuất; ghi riêng tỷ lệ giao hàng quá hạn.
- Với hàng còn hạn bị chê cũ, kiểm tra bao bì/niêm phong và hồ sơ lưu kho.
- Không dùng một nhãn 'expired' chung cho cả hai loại phản hồi.


### Evidence

- [Review #619] (resolved, p4_output): I dont know if.... I dont know if they were fresh or if they were supposed to taste like they did. I checked the expiration date it was current but still tasted kind of stale to me !!!
- [Review #733] (resolved, p4_output): a bit on the stale side. Expiration date 1-13. Smashed and. stale. edible, not real enjoyable for the price I paid, One of the best pretzel's I had when i purchased them from Publix. They stopped carrying them, I must find another addiction.
- [Review #542] (resolved, p4_output): STALE. Beware buying these on special!. I've bought these at the local supermarket and enjoyed them although they are so salty that a few leave my tongue and roof of my mouth burning. Keeps you from eating too many! Occasionally I get really stale items from Amazon.com and this was one. Unedible. Beware of the quality of food items on this website that are on special as they can be very close to due dates or in this case, not expired but stale and unedible just the same.
- [Review #516] (resolved, p4_output): Great Value. Despite coming in an extremely large box, I found this to be great value. All the bags were preserved with a reasonable expiration date that is months away. I'd definitely recommend.
- [POL-FQD-002::pol_POL-FQD-002_3] (resolved, p4_output): [Food Quality, Freshness, and Shelf Life Standards - 2. Sensory & Freshness Integrity]
## 2. Sensory & Freshness Integrity
- **Stale, Rancid, or Off-Flavor Defect (POL-FQD-002.1):** Nuts, oils, whole-grain snacks, and roasted coffee displaying oxidation, bitterness, rancid odors, or stale texture prior to the printed expiration date indicate barrier failure, seal compromise, or warehouse storage above 75°F.
- **Foreign Matter & Contamination (POL-FQD-002.2):** Reports of mold, insects, foreign particles, or discoloration require an immediate batch freeze and notification of the supplier QA lead within 24 hours.
- [POL-FQD-002::pol_POL-FQD-002_2] (resolved, p4_output): [Food Quality, Freshness, and Shelf Life Standards - 1. Expiration & Minimum Shelf Life Thresholds]
## 1. Expiration & Minimum Shelf Life Thresholds
- **Minimum Remaining Shelf Life upon Delivery (POL-FQD-001.1):** All ambient food, snacks, beverages, and pet food dispatched to customers must have at least 60 days of remaining shelf life, or at least 50% of the total manufacturer shelf life (whichever is shorter).
- **Perishable & Fresh Items (POL-FQD-001.2):** Baked goods, artisanal cheese, and fresh produce must have a minimum of 7 days before best-by date upon delivery.
- **Short-Dated Inventory Clearance:** Any SKU within 30 days of the expiration date must be segregated into clearance inventory, flagged explicitly as "Short-Dated", or donated/disposed of. Dispatching expired goods is a zero-tolerance compliance violation.
- [Review #119157] (resolved, p3_example): Stale and expired. I received my sunflower kernels and started munching a bag of them. I noticed a slightly "off" taste, so I checked the expiration date, and they had expired almost two months before I ordered them. Many products are good long past their expiration date and I would not request a refund on food simply because it was expired, but this product did not taste fresh. I reported the problem to Amazon and they immediately refunded my money. While the product was not satisfactory, Amazon's service is, as always, first-rate!
- [Review #234066] (resolved, p3_example): EXPIRED AND STALE. I am very disappointed, received in mail and noticed the expiration date on all packs were 2009, over 2 yrs past this date. Gum was hard as a rock and stale. Buyer BEWARE!
- [Review #237263] (resolved, p3_example): Check the EXPIRATION DATE!!!. These candies are great if they are NOT expired. I have ordered these candies from several different sellers on multiple occasions and I have consistently received expired products. Additionally, some sellers put company stickers over top of the expiration date so you can't tell when the product expires. Beware of the following sellers as I have had trouble with each of them: Toys Samurai, ABCTOY4me and ToysDiva. I have reported each of them to Amazon (4 different complaints in the past 4 months) and Amazon has done nothing to stop them from sending out expired products or products with hidden expiration dates. Good luck.

> Retrieved evidence includes 4–5-star reviews; inspect text rather than inferring sentiment from rating alone.

## #9 — cans / dented / dented cans

- P3 assigned 1605 complaint reviews to this issue.
- 64.2% of assigned complaints are one-star reviews.
- P3 priority score: 19.5/100.
- This group accounts for 2.8% of complaints assigned by P3.
- P2 trend status in 2012-10: stable.
- P2 rolling-window share growth: -9.4% (separate from P3 growth).

### Lon móp bên trong kiện gợi ý cần kiểm tra trước đóng lốc, chưa thể mặc định do giao hàng

P4 #410 khen một loại cá hồi nhưng đồng thời kể lon của loại khác bị móp. Rating 5 sao không làm mất thông tin về kiện còn lại. [Review #410]

P3 #178812, #31982 và #487318 mô tả lon móp bên trong lốc bọc, có trường hợp kiện ngoài vẫn ổn. Đây là lời kể để kiểm tra giả thuyết hư hỏng có trước khâu giao cuối. [Review #178812, Review #31982, Review #487318]

**Diễn giải:** Nhóm 1.605 phàn nàn có một hướng khoanh vùng hữu ích: đối chiếu chất lượng lon trước đóng lốc với tình trạng kiện ngoài, thay vì chỉ tăng vật liệu chèn thùng.

**Chưa thể kết luận:** Review không xác nhận được thời điểm lon móp; phần lớn bằng chứng trực tiếp cho giả thuyết này đến từ P3, không phải P4.

**Hành động đề xuất:**

- Lấy mẫu kiểm tra lon trước bọc lốc và trước xuất kiện.
- Ghi vị trí móp, ảnh lớp bọc và ảnh kiện ngoài để phân biệt các công đoạn.
- Theo dõi lỗi theo nhà cung cấp/lô trước khi quy trách nhiệm cho hãng giao.


### Evidence

- [Review #593] (resolved, p4_output): Great Tasting Chips. After looking at the pictures someone put on here showing a crushed box, I had to write a review. I have bought these chips numerous times from Amazon Warehouse Deals and each time they came packaged perfectly. There was a sale at the end of the summer and I received a few cases/boxes for just over $10.00. The chips were fresh and very hard to eat just one bag. I hid them in the garage and only remembered them when I went out there; that way I didn't eat them all. As far as the pictures, if the person contacted Amazon, he made out ok. Amazon is great with handling complaints and this person was given perfect
- [Review #410] (resolved, p4_output): Great product. I ordered this product at the same time as the Kirkland Signature salmon. The Raincoast Trading Co. salmon is very tasty, equally as good quality salmon as the Kirkland. However, the Raincoast arrived in perfect condition, the Kirkland cans were dented badly. I recommend this product to anyone who likes boneless skinless canned salmon.
- [Review #863] (resolved, p4_output): 3 weeks to actually get to me (maybe it had to be imported) but when it did, it came well packed and not damaged whatsoever. I'm definitely considering re-stocking on this in the future if I can't find a local store EDIT: Oct 11, 2012 *****Inquire the type of pocky from seller before finalizing purchase***** So I decided to restock after I couldn't fight the craving anymore. Unfortunately the batch this time was not so good (ordered from different seller because it was cheaper and through Amazon Prime). What I received was not the picture shown on the front page (2 per pack japanese pocky), it was a 1 per pack pocky~ish thing from Thailand. In my opinion, the 1
- [Review #390] (resolved, p4_output): Valentine gift winner. I bought these for my boyfriend who really likes honey roasted pecans in salads that I have at a couple of restaurants. Plus, he likes nuts, pecans, almonds peanuts. He loved these. I actually ordered 3 cans instead of the gift tin, so he could take one to work, or his place, and stay fresh longer. Although I don't think freshness will be an issue, they won't last long...lol
- [POL-RET-003::pol_POL-RET-003_3] (resolved, p4_output): [Customer Returns, Refunds, and Dispute Resolution Policy - 2. Damage & Quality Complaints Protocol]
## 2. Damage & Quality Complaints Protocol
- **Immediate Resolution SLA (POL-RET-002.1):** Customers reporting transit damage (leaking bottle, broken glass, crushed box) within 30 days of receipt are eligible for:
  1. Full refund to original payment method or instant store credit.
  2. Free 1-business-day expedited replacement shipment.
- **Photo Evidence Requirement:** For orders under $50, no photo proof is required for the first 2 complaint occurrences per customer account. For orders exceeding $50 or recurring claims, an image of the shipping label and damaged item is requested for courier claims.
- [POL-RET-003::pol_POL-RET-003_2] (resolved, p4_output): [Customer Returns, Refunds, and Dispute Resolution Policy - 1. Non-Returnable Perishable & Food Items]
## 1. Non-Returnable Perishable & Food Items
- **Health & Safety Prohibition (POL-RET-001.1):** For hygiene and food safety reasons, opened or unopened grocery and food products cannot be physically returned to fulfillment centers.
- **"Returnless Refund" Guarantee (POL-RET-001.2):** When a customer reports spoiled, damaged, stale, or incorrect food items, customer service representatives are authorized to issue an instant full refund or replacement without requesting return shipment.
- [Review #487318] (resolved, p3_example): cans dented, crushed. I have been buying this for some time and a few cans were dented. The last shipment (which will be my last shipment) was really bad. Out of the 24 cans I would only use 7 cans. Since these are overwrapped in packs of six, the damage must have happened before the overwrapping was done, since there is no way the dents and crushed cans could have happened during shipping. When I was buying this dog food at the supermarket there would be dented cans on the shelf, but I didn't have to buy them. I didn't expect cans to be so badly damaged when they were being shipped direct from factory.
- [Review #178812] (resolved, p3_example): Severely dented cans.. This is an excellent product. I signed up for the subscription, we like it so much. However, with my first shipment, every single can arrived dented. The problem was not in the outside packaging - that was fine. But the cans, inside the shrink-wrapped case, were dented - on the inside surfaces of the cans! You couldn't see the dents until the cans were unwrapped. So the problem wasn't in the shipping, at least to me, but in shrink wrapping already damaged cans. Will be cancelling my subscription if my next shipment also arrives dented.
- [Review #31982] (resolved, p3_example): So disappointed in canned pumpkin. I read the last few reviews indicating no dented cans and hoped for the best. My box arrived today and I too received badly damaged, dented and unusable cans. I'm not terribly picky but most cans are dented at the rims/seams and all are badly smashed all over. This was my last hope for canned pumpkin for my dog. I do not believe the Amazon packaging is the problem. The cans were already dented prior to being shrink-wrapped. I do not believe stores would put these cans on their shelves and I would never buys cans with this much damage. I have never been unhappy with an Amazon purchase, but this product was a waste of my time.

> Retrieved evidence includes 4–5-star reviews; inspect text rather than inferring sentiment from rating alone.

## #10 — not taste / taste like / tastes like

- P3 assigned 3078 complaint reviews to this issue.
- 55.1% of assigned complaints are one-star reviews.
- P3 priority score: 14.5/100.
- This group accounts for 5.4% of complaints assigned by P3.
- P2 trend status in 2012-10: stable.
- P2 rolling-window share growth: +0.7% (separate from P3 growth).

### Khoảng cách giữa hương vị được mô tả và vị khách cảm nhận là một hướng cải thiện thông tin

P4 #68 kỳ vọng vị xoài nhưng cảm nhận gần cam thảo; #27 chê kẹo chỉ có màu mà thiếu vị. Đây là mô tả về kỳ vọng và cảm nhận, không tự động là sản phẩm hỏng. [Review #68, Review #27]

Ví dụ P3 #341866 phản ánh mô tả 'hints' về vị trái cây không đáp ứng kỳ vọng độ đậm; #429673 kỳ vọng vị bắp rang rạp chiếu phim nhưng cảm nhận nhạt. [Review #341866, Review #429673]

**Diễn giải:** Với 3.078 phàn nàn, nhóm này gợi ý thử mô tả độ đậm/hậu vị rõ hơn và kiểm tra kỳ vọng theo từng sản phẩm. Chủ đề gần nhóm tasted và weak; chưa nên coi là ba căn nguyên riêng biệt.

**Chưa thể kết luận:** Chưa có thử nếm có kiểm soát để phân biệt sai mô tả, khác sở thích hay biến động chất lượng.

**Hành động đề xuất:**

- Đối chiếu mô tả hương vị với phản hồi theo SKU.
- Phân biệt 'không có vị', 'không giống vị quảng bá' và 'vị lạ/bất thường'.
- Rà soát khả năng gộp hoặc định nghĩa lại các nhóm vị đang trùng chủ đề trước khi làm dashboard quản trị.


### Evidence

- [Review #68] (resolved, p4_output): Taste is not so good.. I purchased the Mango flavor, and to me it doesn't take like Mango at all. There is no hint of sweetness, and unfortunately there is a hint or aftertaste almost like licorice. I've been consuming various sports nutrition products for decades, so I'm familiar and have come to like the taste of the most of the products I've tried. The mango flavor is one of the least appealing I've tasted. It's not terrible, but it's bad enough that I notice the bad taste every sip I take.
- [Review #335] (resolved, p4_output): Does not taste very good. Taste like it is stale. Will not order this again. I had this coffee at a 50th year annerversery at a reception hall and had to have it. This stuff tasted NOTHING, like the Douwe Egberts at the hall. This is possibly stale coffee.
- [Review #27] (resolved, p4_output): Nasty No flavor. The candy is just red , No flavor . Just plan and chewy . I would never buy them again
- [Review #863] (resolved, p4_output): your mouth. Personally I like the taste of dark chocolate but not when used here as a pocky flavor. I also have terrible self control so I buy things that come in small portions in order to a) not eat everything at once and b) avoid making the fridge a mess by cluttering it with tons of opened items. I can honestly say that I won't be overeating when it comes to this batch of pocky because I and my stomach dislike it so much. I won't change my original rating because that still holds true for the Japanese pocky but if I were to rate only the Thailand pocky it would be a 3. The taste isn't "terrible" but
- [POL-RET-003::pol_POL-RET-003_4] (resolved, p4_output): [Customer Returns, Refunds, and Dispute Resolution Policy - 3. Product Reformulation / Dislike Discontent]
## 3. Product Reformulation / Dislike Discontent
- **Taste Satisfaction Guarantee (POL-RET-003.1):** If a customer dislikes the flavor, texture, or finds a recipe change unsatisfactory within 14 days, support grants a one-time courtesy credit equal to the product value.
- **Recurring Issue Escalation:** When 5 or more distinct customers complain about the same batch code for off-taste or early spoilage within a 7-day window, the SKU must be automatically paused from new order dispatch pending merchant review.
- [POL-FQD-002::pol_POL-FQD-002_3] (resolved, p4_output): [Food Quality, Freshness, and Shelf Life Standards - 2. Sensory & Freshness Integrity]
## 2. Sensory & Freshness Integrity
- **Stale, Rancid, or Off-Flavor Defect (POL-FQD-002.1):** Nuts, oils, whole-grain snacks, and roasted coffee displaying oxidation, bitterness, rancid odors, or stale texture prior to the printed expiration date indicate barrier failure, seal compromise, or warehouse storage above 75°F.
- **Foreign Matter & Contamination (POL-FQD-002.2):** Reports of mold, insects, foreign particles, or discoloration require an immediate batch freeze and notification of the supplier QA lead within 24 hours.
- [Review #429673] (resolved, p3_example): Not that great. This popcorn oil has a rather bland taste and is not that great. It tastes like it has no salt in it at all. I won't buy it again. Does not taste like movie theater popcorn.
- [Review #366684] (resolved, p3_example): chocolate dip yuck. I was so excited when I found this chocolate dip. When I received the dip, I tried it and almost threw it up. This dip taste so bad, and it does not even taste like chocolate.
- [Review #341866] (resolved, p3_example): What flavor?. "A delicate tea with enticing hints of blueberry & white cranberry" "Delicate" and "hints" should've been the first tip off, translation: this tea has no flavor. Zip. I've tried other blueberry teas, and not only does the actual color of the tea change, it -tastes- like blueberries. I expected some flavor, especially with the cranberry, but nuthin. The only reason I didn't give this one star is that it at least didn't taste bad. It just didn't taste like anything.

> Retrieved evidence includes 4–5-star reviews; inspect text rather than inferring sentiment from rating alone.

## #11 — weak / pods / bland

- P3 assigned 4316 complaint reviews to this issue.
- 45.2% of assigned complaints are one-star reviews.
- P3 priority score: 14.1/100.
- This group accounts for 7.6% of complaints assigned by P3.
- P2 trend status in 2012-10: stable.
- P2 rolling-window share growth: -2.6% (separate from P3 growth).

### Độ đậm cà phê là tín hiệu từ ví dụ P3; kết quả P4 đang có nhiễu từ nghĩa của từ weak

P4 #469 dùng weak at the knees để khen snack, không phải chê cà phê nhạt. #371 có cả nhận xét chê một số blend và khen blend khác, xuất hiện thành hai chunk. [Review #469, Review #371]

P3 #254274 nói phải dùng hai pod, #156806 nói tăng tỷ lệ cà phê/nước vẫn nhạt; đây là bằng chứng phù hợp hơn cho hướng điều tra độ đậm. [Review #254274, Review #156806]

**Diễn giải:** Nhóm có 4.316 phàn nàn nhưng tỷ lệ 1 sao 45,2% thấp hơn các nhóm đứng đầu. Có thể ưu tiên rà soát kỳ vọng độ đậm và cách pha; chưa đủ cơ sở xác nhận lỗi định lượng pod.

**Chưa thể kết luận:** Chưa có thông số pha, loại máy, khối lượng cà phê hoặc thử nếm; P4 chưa truy xuất được nhiều ví dụ trực tiếp phù hợp.

**Hành động đề xuất:**

- Ghi loại máy, cỡ cốc, tỷ lệ pha và blend trong mẫu rà soát.
- Đọc nội dung để loại kết quả weak mang nghĩa thành ngữ khi phân tích P5.
- Đối chiếu hướng dẫn và mô tả độ đậm trước khi đề xuất thay đổi công thức.


### Evidence

- [Review #371] (resolved, p4_output): A saving grace for Green Mountain Coffee.... When we received our Keurig Elite for Christmas, we were so excited to break open the sample pack of pods to try out different blends and flavors. Of the 12 pods we had in the box, four were Green Mountain Coffee brand. I'd never tried anything from this company before, but from what I had researched online, they have the largest range of Keurig pods and have even bought out competitors to produce coffee under their brand names as well. Unfortunately, I was immediately disappointed by the quality of the coffee. We tried their Dark Magic, Decaf and Breakfast Blend and all were underwhelming, to say the least. I was almost completely set
- [Review #371] (resolved, p4_output): their Dark Magic, Decaf and Breakfast Blend and all were underwhelming, to say the least. I was almost completely set on writing off Green Mountain altogther. We had one GM pod left and being of the mindset of waste-not-want-not, I figured I'd give it one last go around before forgetting about them completely. And I'm glad I did. The Nantucket Blend is a perfectly pleasing cup of coffee. It is nice and flavorful without being thick and pungent (unlike some of the other GM blends we tried). I added some flavored creamer to it and it almost measures up to our go-to Caribou Blend pods. Almost. All in all, this is a very standard cup of coffee which, while it
- [Review #469] (resolved, p4_output): These chips make me weak at the knees. These chips remind me of a long obsolete brand of chips we could get in middle school. They are by far the tastiest chips I've had and it's impossible to walk past the aisle without picking up the trademark blue bag and then putting the bag clip on the bag!
- [Review #831] (resolved, p4_output): Excellent. Nice flavor, not too bitter. We really like this coffee. We have been searching for a coffee that pleases the whole family's tastes and this is the one.
- [POL-RET-003::pol_POL-RET-003_4] (resolved, p4_output): [Customer Returns, Refunds, and Dispute Resolution Policy - 3. Product Reformulation / Dislike Discontent]
## 3. Product Reformulation / Dislike Discontent
- **Taste Satisfaction Guarantee (POL-RET-003.1):** If a customer dislikes the flavor, texture, or finds a recipe change unsatisfactory within 14 days, support grants a one-time courtesy credit equal to the product value.
- **Recurring Issue Escalation:** When 5 or more distinct customers complain about the same batch code for off-taste or early spoilage within a 7-day window, the SKU must be automatically paused from new order dispatch pending merchant review.
- [POL-FQD-002::pol_POL-FQD-002_3] (resolved, p4_output): [Food Quality, Freshness, and Shelf Life Standards - 2. Sensory & Freshness Integrity]
## 2. Sensory & Freshness Integrity
- **Stale, Rancid, or Off-Flavor Defect (POL-FQD-002.1):** Nuts, oils, whole-grain snacks, and roasted coffee displaying oxidation, bitterness, rancid odors, or stale texture prior to the printed expiration date indicate barrier failure, seal compromise, or warehouse storage above 75°F.
- **Foreign Matter & Contamination (POL-FQD-002.2):** Reports of mold, insects, foreign particles, or discoloration require an immediate batch freeze and notification of the supplier QA lead within 24 hours.
- [Review #254274] (resolved, p3_example): coffee pods. I expected full-bodied Columbian flavor as in other brand pods. However it was so weak in even a 6oz cup that i had to use 2 pods. Very disappointing. But did receive it quickly. Good if you like weak coffee
- [Review #3871] (resolved, p3_example): Very weak coffee. I have a Melitta One:One machine and have been using Juan Valdez pods in it. When I ran out I searched for pods for it & only came up with these Melitta-brand ones. I figured (incorrectly) that the others weren't available & purchased these. VERY disappointing. My coffee had been nice, strong & tasty, but coffee made with these is weak & tasteless. I bought a 4-box package of three different types & am now stuck with them. Forget these & head to Juan Valdez (same price range) unless you like weak coffee.
- [Review #156806] (resolved, p3_example): Smooth, but weak. This coffee is weak and bland. I used a high ratio of coffee to water and it still came out tasteless. I was very disappointed, especially since I bought a 2.5 lb bag. I'm going to have to mix it with much stronger coffee or throw it out. I could not taste the kona at all. If you are looking for robust kona blend coffee, don't waste your money. On the other hand if you like weak coffee, you may like this. It is smooth, not bitter or acidic.

> Retrieved evidence includes 4–5-star reviews; inspect text rather than inferring sentiment from rating alone.

## #12 — bitter / bitter taste / aftertaste

- P3 assigned 2171 complaint reviews to this issue.
- 54.0% of assigned complaints are one-star reviews.
- P3 priority score: 12/100.
- This group accounts for 3.8% of complaints assigned by P3.
- P2 trend status in 2012-10: stable.
- P2 rolling-window share growth: -9.8% (separate from P3 growth).

### Vị đắng/hậu vị cần phân biệt giữa sở thích, công thức và chất lượng theo lô

P4 #362 mô tả cà phê vẫn đắng dù thêm kem/mật ong; #68 mô tả hậu vị gần cam thảo. #661 lại khen không có hậu vị đắng, nên không thể coi mọi kết quả là phàn nàn. [Review #362, Review #68, Review #661]

P3 #303450 nhận xét nước ép chua/đắng nhưng thừa nhận khác biệt khẩu vị; #291426 nói phải thêm đường/kem vì vị đắng. [Review #303450, Review #291426]

**Diễn giải:** Trong 2.171 phàn nàn, các ví dụ cho thấy trải nghiệm vị có tính chủ quan và phụ thuộc sản phẩm. Hướng phù hợp là phân loại hậu vị theo SKU và kiểm tra tính ổn định, chưa phải kết luận chung về bảo quản kém.

**Chưa thể kết luận:** Chưa biết tỷ lệ do công thức, rang/pha, sở thích hay chất lượng; chưa có so sánh cùng SKU giữa các lô.

**Hành động đề xuất:**

- So sánh phản hồi vị đắng theo SKU/lô và cách sử dụng.
- Mô tả rõ hậu vị trên trang bán khi đó là đặc trưng dự kiến của sản phẩm.
- Theo dõi cụm phản hồi tương tự trong cùng lô để chọn mẫu kiểm tra cảm quan.


### Evidence

- [Review #362] (resolved, p4_output): Bitter. A very bitter tasting coffee even when enhanced with cream and/or honey. Definately not my cup of coffee. Oh, did i say it was bitter?
- [Review #68] (resolved, p4_output): Taste is not so good.. I purchased the Mango flavor, and to me it doesn't take like Mango at all. There is no hint of sweetness, and unfortunately there is a hint or aftertaste almost like licorice. I've been consuming various sports nutrition products for decades, so I'm familiar and have come to like the taste of the most of the products I've tried. The mango flavor is one of the least appealing I've tasted. It's not terrible, but it's bad enough that I notice the bad taste every sip I take.
- [Review #661] (resolved, p4_output): Great stuff!. I love using this to sweeten tea, coffee, etc. It tastes much better than other low glycemic sweeteners - there is no bitter aftertaste.
- [Review #335] (resolved, p4_output): Does not taste very good. Taste like it is stale. Will not order this again. I had this coffee at a 50th year annerversery at a reception hall and had to have it. This stuff tasted NOTHING, like the Douwe Egberts at the hall. This is possibly stale coffee.
- [POL-RET-003::pol_POL-RET-003_4] (resolved, p4_output): [Customer Returns, Refunds, and Dispute Resolution Policy - 3. Product Reformulation / Dislike Discontent]
## 3. Product Reformulation / Dislike Discontent
- **Taste Satisfaction Guarantee (POL-RET-003.1):** If a customer dislikes the flavor, texture, or finds a recipe change unsatisfactory within 14 days, support grants a one-time courtesy credit equal to the product value.
- **Recurring Issue Escalation:** When 5 or more distinct customers complain about the same batch code for off-taste or early spoilage within a 7-day window, the SKU must be automatically paused from new order dispatch pending merchant review.
- [POL-FQD-002::pol_POL-FQD-002_3] (resolved, p4_output): [Food Quality, Freshness, and Shelf Life Standards - 2. Sensory & Freshness Integrity]
## 2. Sensory & Freshness Integrity
- **Stale, Rancid, or Off-Flavor Defect (POL-FQD-002.1):** Nuts, oils, whole-grain snacks, and roasted coffee displaying oxidation, bitterness, rancid odors, or stale texture prior to the printed expiration date indicate barrier failure, seal compromise, or warehouse storage above 75°F.
- **Foreign Matter & Contamination (POL-FQD-002.2):** Reports of mold, insects, foreign particles, or discoloration require an immediate batch freeze and notification of the supplier QA lead within 24 hours.
- [Review #208992] (resolved, p3_example): Bitter aftertaste. I just threw out a batch of hummus made with this tahini because it had an overwhelming bitter taste to it. Bitter in the same way that the motionsickness medicine Dramamine is bitter. Will not buy this brand again.
- [Review #303450] (resolved, p3_example): Very Tart and Somewhat bitter Taste. Everyone's taste buds are different, but I personally thought that this juice was a bit extreme. It is very tart and has a slight bitter aftertaste. If you have never tried this flavor, I'd recommend purchasing it in smaller quantities to check the taste. I won't say that we are stuck with 38 boxes, I'm sure I'll eventually drink them, but it will be a last choice. This flavor is just not for me.
- [Review #291426] (resolved, p3_example): Bitter. I think that's the only way to describe this coffee: bitter. I don't use creamer or sugar in my coffee but with this one I have to add something to offset the bitter taste.

> Retrieved evidence includes 4–5-star reviews; inspect text rather than inferring sentiment from rating alone.
