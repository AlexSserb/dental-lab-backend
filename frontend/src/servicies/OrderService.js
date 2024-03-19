import axios from "axios";

const API_URL = "api/";

class OrderService {
  getOrdersForUser(page) {
    return axios.get(API_URL + `orders_for_physician/?page=${page}`);
  }

  getOrders(month, year) {
    return axios.get(API_URL + `orders/${year}/${month}`);
  }

  post(order) {
    return axios.post(API_URL + "create_order/", { "product_types": order });
  }
}

const orderService = new OrderService();
export default orderService;
