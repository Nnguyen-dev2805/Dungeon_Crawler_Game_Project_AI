# DUNGEON CRAWLER: ỨNG DỤNG THUẬT TOÁN TÌM KIẾM VÀ AI CHO KẺ THÙ

- HCMC University of Technology and Education  
- **Môn**: Trí Tuệ Nhân Tạo  
- **Giảng viên hướng dẫn**: TS. Phan Thị Huyền Trang  

Dự án được phát triển dựa trên nền tảng Pygame, tập trung vào việc xây dựng một game **Dungeon Crawler** 2D với kẻ thù thông minh. Điểm nổi bật là hệ thống AI của kẻ thù, ứng dụng các thuật toán tìm kiếm và học máy để tạo ra hành vi thực tế, bao gồm tuần tra, tấn công, và chạy trốn.

![DEMO](assets/demo.gif)

---

## 🧠 Các thuật toán và cách hoạt động

### 🌟 A* (A-star Search) – Tìm đường tối ưu

- **Mục tiêu:** Giúp kẻ thù di chuyển đến mục tiêu một cách nhanh chóng và hiệu quả.
- **Cách hoạt động:**  
  - Dựa trên công thức:  `f(state) = g(state) + h(state)`
    - `g(state)`: Chi phí từ điểm bắt đầu đến vị trí hiện tại.
    - `h(state)`: Ước lượng khoảng cách từ vị trí hiện tại đến mục tiêu (dùng heuristic Manhattan).
  - Ưu tiên mở rộng các ô có chi phí tổng nhỏ nhất để tìm đường đi ngắn nhất.
- **Ứng dụng trong game:**  
  - Kẻ thù dùng A* để đuổi theo người chơi khi nhìn thấy hoặc để chạy trốn đến vị trí an toàn.
  - Đảm bảo di chuyển tránh được chướng ngại vật và đi theo đường ngắn nhất.

---

### 🔍 Belief Map – Bản đồ niềm tin

- **Mục tiêu:** Giúp kẻ thù dự đoán vị trí người chơi khi không còn nhìn thấy.
- **Cách hoạt động:**  
  - Khi nhìn thấy người chơi, kẻ thù cập nhật bản đồ niềm tin, tăng giá trị cho các ô xung quanh vị trí người chơi.
  - Khi mất dấu, kẻ thù giảm niềm tin ở khu vực xung quanh vị trí hiện tại của mình và tăng niềm tin ở các khu vực chưa khám phá.
  - Dựa trên bản đồ niềm tin, kẻ thù chọn ô có giá trị cao nhất để di chuyển đến, kết hợp với A* để tìm đường.
- **Ứng dụng:**  
  - Kẻ thù tuần tra thông minh, không di chuyển ngẫu nhiên mà tập trung vào các khu vực có khả năng cao người chơi đang ẩn nấp.

---

### ⛰️ Q-Learning – Tự học hành vi tuần tra

- **Mục tiêu:** Giúp kẻ thù học cách tuần tra hiệu quả qua trải nghiệm.
- **Cách hoạt động:**  
  - Kẻ thù lưu trữ kinh nghiệm trong bảng Q, mỗi ô tương ứng với cặp trạng thái và hành động.
  - Cập nhật giá trị Q theo công thức:  
    `Q[state][action] = Q[state][action] + α * (r + γ * max(Q[state'][action']) - Q[state][action])`
    - `state`: Trạng thái hiện tại (khoảng cách đến người chơi, máu, tầm nhìn, v.v.).
    - `action`: Hành động (di chuyển lên, xuống, trái, phải).
    - `r`: Phần thưởng (gần người chơi, khám phá khu vực mới, v.v.).
    - `α`: Tốc độ học.
    - `γ`: Hệ số chiết khấu.
  - Kẻ thù chọn hành động dựa trên chiến lược ε-greedy:
    - Xác suất ε: Chọn hành động ngẫu nhiên để khám phá.
    - Xác suất 1-ε: Chọn hành động tốt nhất từ bảng Q để khai thác kinh nghiệm.
- **Ứng dụng:**  
  - Kẻ thù học cách tuần tra hiệu quả, ưu tiên các khu vực có khả năng cao tìm thấy người chơi.
  - Có thể thay thế Belief Map, giúp giảm tính toán và tạo hành vi linh hoạt hơn.

---

### 🛠️ Các thuật toán tìm kiếm khác

- **BFS (Breadth-First Search):**  
  Tìm đường ngắn nhất bằng cách duyệt theo chiều rộng.  
  Dùng để đuổi theo người chơi, đảm bảo đường đi ngắn nhất nhưng không nhanh bằng A*.

- **Beam Search:**  
  Tìm đường bằng cách giữ lại một số lựa chọn tốt nhất ở mỗi bước.  
  Nhanh hơn A* trên bản đồ lớn nhưng có thể không tìm được đường tối ưu.

- **Backtracking Search:**  
  Tìm đường bằng cách thử và quay lui.  
  Dùng trong các tình huống phức tạp nhưng chậm hơn các thuật toán khác.

- **Ứng dụng:**  
  Các thuật toán này được dùng để đuổi theo người chơi, giúp kẻ thù có nhiều lựa chọn chiến lược khác nhau.

---

## 🔥 Cách game hoạt động

**Khởi tạo:**  
- Bản đồ được tải từ file CSV, tạo thành lưới ô với các vị trí tường và ô trống.
- Người chơi và kẻ thù được đặt ở các vị trí ban đầu, với các thông số như máu và hình ảnh hoạt hình.

**Vòng lặp chính:**  
- Mỗi khung hình, kẻ thù quyết định hành vi:
  - Nếu nhìn thấy người chơi trong tầm phát hiện, kẻ thù đuổi theo hoặc tấn công.
  - Nếu không thấy người chơi, kẻ thù tuần tra dựa trên bản đồ niềm tin hoặc Q-Learning.
  - Nếu máu thấp, kẻ thù chạy trốn và tìm vị trí an toàn để hồi máu.
- Người chơi di chuyển, tấn công, và thu thập vật phẩm (tiền xu, bình máu) do kẻ thù thả khi chết.

**Di chuyển:**  
- Kẻ thù di chuyển theo lưới ô, nhưng chuyển động thực tế được tính bằng pixel để mượt mà.
- Hỗ trợ di chuyển 4 hướng chính (lên, xuống, trái, phải) và 4 hướng chéo (ví dụ: trái lên, phải xuống).

**Tấn công và chạy trốn:**  
- Kẻ thù tấn công người chơi nếu ở gần, gây sát thương trực tiếp hoặc bắn đạn (nếu là boss).
- Khi máu thấp, kẻ thù chạy trốn, tìm vị trí xa người chơi và gần tường, đồng thời hồi máu định kỳ.

**Vẽ lên màn hình:**  
- Hiển thị bản đồ, người chơi, kẻ thù, và vật phẩm.
- Thanh máu của kẻ thù và vòng phát hiện được vẽ để người chơi dễ theo dõi.

---

## 👨‍💻 Thành viên phát triển

| Họ và tên        | Mã sinh viên  |
|------------------|---------------|
| Trương Nhất Nguyên | 23110273      |
| Đặng Ngọc Tài  | 23110304      |

---

## 🧰 Yêu cầu hệ thống

- Python 3.x  
- Thư viện `pygame`

---

## 🚀 Hướng dẫn cài đặt & chạy game

### 1. Tải mã nguồn
```bash
git clone https://github.com/Nnguyen-dev2805/Dungeon_Crawler_Game_Project_AI.git
```
### 2. Cài đặt thư viện cần thiết
```bash
pip install pygame
```
### 3. Chạy game
```bash
python main.py
```
