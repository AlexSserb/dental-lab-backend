import axios from "axios";

const API_URL = "api/";

class OrderService {
  getOrdersForUser() {
    return axios.get(API_URL + "orders/");
  }

  post(order) {
    return axios.post(API_URL + "create_order/", { "product_types": order });
  }
}

const orderService = new OrderService();
export default orderService;
