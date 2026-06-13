# Hướng Dẫn Kết Nối pgAdmin Chi Tiết (10 Databases)

Để thêm các database vào pgAdmin, bạn click chuột phải vào **Servers** -> chọn **Register** -> **Server...** rồi điền chính xác thông tin ở 2 Tab **General** và **Connection** như sau:

---

## 1. Dịch Vụ Xác Thực & Người Dùng (`auth_db`)
*   **Tab General:**
    *   `Name` (ServerName): `TruongShop - Auth DB`
*   **Tab Connection:**
    *   `Host name/address`: `localhost`
    *   `Port`: `5432`
    *   `Maintenance database`: `auth_db`
    *   `Username`: `auth_user`
    *   `Password`: `auth_pass`

---

## 2. Dịch Vụ Quản Lý Sản Phẩm (`product_db`)
*   **Tab General:**
    *   `Name` (ServerName): `TruongShop - Product DB`
*   **Tab Connection:**
    *   `Host name/address`: `localhost`
    *   `Port`: `5437`
    *   `Maintenance database`: `product_db`
    *   `Username`: `product_user`
    *   `Password`: `product_pass`

---

## 3. Dịch Vụ Giỏ Hàng (`cart_db`)
*   **Tab General:**
    *   `Name` (ServerName): `TruongShop - Cart DB`
*   **Tab Connection:**
    *   `Host name/address`: `localhost`
    *   `Port`: `5436`
    *   `Maintenance database`: `cart_db`
    *   `Username`: `cart_user`
    *   `Password`: `cart_pass`

---

## 4. Dịch Vụ Đơn Hàng (`order_db`)
*   **Tab General:**
    *   `Name` (ServerName): `TruongShop - Order DB`
*   **Tab Connection:**
    *   `Host name/address`: `localhost`
    *   `Port`: `5438`
    *   `Maintenance database`: `order_db`
    *   `Username`: `order_user`
    *   `Password`: `order_pass`

---

## 5. Dịch Vụ Thanh Toán (`payment_db`)
*   **Tab General:**
    *   `Name` (ServerName): `TruongShop - Payment DB`
*   **Tab Connection:**
    *   `Host name/address`: `localhost`
    *   `Port`: `5439`
    *   `Maintenance database`: `payment_db`
    *   `Username`: `payment_user`
    *   `Password`: `payment_pass`

---

## 6. Dịch Vụ Khuyến Mãi (`voucher_db`)
*   **Tab General:**
    *   `Name` (ServerName): `TruongShop - Voucher DB`
*   **Tab Connection:**
    *   `Host name/address`: `localhost`
    *   `Port`: `5440`
    *   `Maintenance database`: `voucher_db`
    *   `Username`: `voucher_user`
    *   `Password`: `voucher_pass`

---

## 7. Dịch Vụ Đánh Giá Sản Phẩm (`rating_db`)
*   **Tab General:**
    *   `Name` (ServerName): `TruongShop - Rating DB`
*   **Tab Connection:**
    *   `Host name/address`: `localhost`
    *   `Port`: `5441`
    *   `Maintenance database`: `rating_db`
    *   `Username`: `rating_user`
    *   `Password`: `rating_pass`

---

## 8. Dịch Vụ Nhà Cung Cấp (`supplier_db`)
*   **Tab General:**
    *   `Name` (ServerName): `TruongShop - Supplier DB`
*   **Tab Connection:**
    *   `Host name/address`: `localhost`
    *   `Port`: `5442`
    *   `Maintenance database`: `supplier_db`
    *   `Username`: `supplier_user`
    *   `Password`: `supplier_pass`

---

## 9. Dịch Vụ Theo Dõi Hành Vi (`tracking_db`)
*   **Tab General:**
    *   `Name` (ServerName): `TruongShop - Tracking DB`
*   **Tab Connection:**
    *   `Host name/address`: `localhost`
    *   `Port`: `5443`
    *   `Maintenance database`: `tracking_db`
    *   `Username`: `tracking_user`
    *   `Password`: `tracking_pass`

---

## 10. Dịch Vụ Chatbot RAG (`chatbot_db`)
*   **Tab General:**
    *   `Name` (ServerName): `TruongShop - Chatbot DB`
*   **Tab Connection:**
    *   `Host name/address`: `localhost`
    *   `Port`: `5444`
    *   `Maintenance database`: `chatbot_db`
    *   `Username`: `chatbot_user`
    *   `Password`: `chatbot_pass`
