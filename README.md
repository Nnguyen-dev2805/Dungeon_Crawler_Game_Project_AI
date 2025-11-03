<div align="center">

# DUNGEON CRAWLER AI

### Hệ thống kẻ thù thông minh sử dụng thuật toán tìm kiếm và học máy

[![Python](https://img.shields.io/badge/Python-3.x-blue.svg)](https://www.python.org/)
[![Pygame](https://img.shields.io/badge/Pygame-2.x-green.svg)](https://www.pygame.org/)
[![License](https://img.shields.io/badge/License-MIT-yellow.svg)](LICENSE)

</div>

---

## Thông tin đề tài

- **Trường**: Đại học Sư phạm Kỹ thuật TP.HCM (HCMUTE)
- **Môn học**: Trí tuệ nhân tạo
- **Giảng viên hướng dẫn**: TS. Phan Thị Huyền Trang
- **Sinh viên thực hiện**: 
  - Trương Nhất Nguyên - 23110273
  - Đặng Ngọc Tài - 23110304

---

## Mô tả dự án

Dự án xây dựng game **Dungeon Crawler** 2D với Pygame, tập trung vào hệ thống AI kẻ thù thông minh sử dụng các thuật toán tìm kiếm và học máy. Kẻ thù có khả năng tuần tra, truy đuổi, tấn công và chạy trốn dựa trên các điều kiện động trong game. Hệ thống AI kết hợp nhiều thuật toán tìm đường (A*, BFS, Beam Search) với bản đồ niềm tin và học tăng cường (Q-Learning) để tạo ra lối chơi thử thách và thích ứng.

![DEMO](assets/demo.gif)

---

## Mục lục

- [Tính năng chính](#tính-năng-chính)
- [Các thuật toán AI](#các-thuật-toán-ai)
  - [A* Search](#a-a-star-search--tìm-đường-tối-ưu)
  - [Belief Map](#belief-map--bản-đồ-niềm-tin)
  - [Q-Learning](#q-learning--tự-học-hành-vi-tuần-tra)
  - [Các thuật toán tìm kiếm khác](#các-thuật-toán-tìm-kiếm-khác-1)
- [Cách game hoạt động](#cách-game-hoạt-động)
- [Yêu cầu hệ thống](#yêu-cầu-hệ-thống)
- [Hướng dẫn cài đặt](#hướng-dẫn-cài-đặt--chạy-game)

---

## Tính năng chính

- **AI kẻ thù thông minh**: Sử dụng các thuật toán tìm đường tiên tiến (A*, BFS, Beam Search) để di chuyển trong dungeon
- **Hệ thống niềm tin**: Kẻ thù dự đoán vị trí người chơi bằng belief map khi không nhìn thấy
- **Học tăng cường**: Triển khai Q-Learning cho hành vi tuần tra thích ứng
- **Chiến đấu động**: Hệ thống chiến đấu thời gian thực với quản lý máu và vật phẩm rơi
- **Nhiều hành vi**: Kẻ thù có thể tuần tra, đuổi theo, tấn công và chạy trốn chiến lược khi máu thấp
- **Thiết kế level bằng CSV**: Dễ dàng chỉnh sửa bố cục level
- **Animation mượt mà**: Chuyển động và hoạt hình nhân vật trôi chảy
- **Hệ thống âm thanh**: Nhạc nền và hiệu ứng âm thanh sống động

---

## Các thuật toán AI

### A* (A-star Search) – Tìm đường tối ưu

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

### Belief Map – Bản đồ niềm tin

- **Mục tiêu:** Giúp kẻ thù dự đoán vị trí người chơi khi không còn nhìn thấy.
- **Cách hoạt động:**  
  - Khi nhìn thấy người chơi, kẻ thù cập nhật bản đồ niềm tin, tăng giá trị cho các ô xung quanh vị trí người chơi.
  - Khi mất dấu, kẻ thù giảm niềm tin ở khu vực xung quanh vị trí hiện tại của mình và tăng niềm tin ở các khu vực chưa khám phá.
  - Dựa trên bản đồ niềm tin, kẻ thù chọn ô có giá trị cao nhất để di chuyển đến, kết hợp với A* để tìm đường.
- **Ứng dụng:**  
  - Kẻ thù tuần tra thông minh, không di chuyển ngẫu nhiên mà tập trung vào các khu vực có khả năng cao người chơi đang ẩn nấp.

---

### Q-Learning – Tự học hành vi tuần tra

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

### Các thuật toán tìm kiếm khác

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

## Cách game hoạt động

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

## Yêu cầu hệ thống

- Python 3.x  
- Thư viện `pygame`

---

## Hướng dẫn cài đặt & chạy game

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

---

## Điều khiển game

- **Phím mũi tên / WASD**: Di chuyển người chơi
- **Chuột trái**: Tấn công
- **ESC**: Tạm dừng game

---

## Công nghệ sử dụng

- **Python 3.x**: Ngôn ngữ lập trình chính
- **Pygame**: Framework phát triển game
- **CSV**: Lưu trữ dữ liệu level
- **NumPy**: Tính toán toán học cho thuật toán AI

---

## Cấu trúc dự án

```
Dungeon_Crawler_Game_Project_AI/
├── main.py           # Vòng lặp game chính và khởi tạo
├── player.py         # Class nhân vật người chơi
├── enemy.py          # Logic AI và hành vi kẻ thù
├── weapon.py         # Hệ thống vũ khí
├── item.py           # Vật phẩm và đồ sưu tầm
├── world.py          # Quản lý thế giới và level
├── algorithms.py     # Thuật toán tìm đường AI
├── qlearning.py      # Triển khai Q-Learning
├── constants.py      # Hằng số và cấu hình game
├── button.py         # Component nút UI
├── assets/           # Tài nguyên game (sprites, audio, fonts)
└── levels/           # Dữ liệu level (file CSV)
```

---

## Liên hệ

Nếu có câu hỏi hoặc phản hồi, vui lòng liên hệ:

- **Trương Nhất Nguyên**: [GitHub](https://github.com/Nnguyen-dev2805)

---

<div align="center">

**Được phát triển bởi Trương Nhất Nguyên & Đặng Ngọc Tài**

</div>
