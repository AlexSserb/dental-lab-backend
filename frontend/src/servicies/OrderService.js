import axios from "axios";

const API_URL = "api/";

class OrderService {
  getOrdersForUser(page) {
    return axios.get(API_URL + `orders-for-physician/?page=${page}`);
  }

  getOrders(month, year) {
    return axios.get(API_URL + `orders/${year}/${month}`);
  }

  post(order) {
    return axios.post(API_URL + "create-order/", { product_types: order });
  }

  // Administrator confirm the order and set the final discounts 
  confirmOrder(order, products) {
    return axios.post(API_URL + "confirm-order/", { order: order, products: products });
  }
}

const orderService = new OrderService();
export default orderService;
