import axios from "axios";

const API_URL = "api/";

class OrderService {
  getOrdersForUser(page) {
    return axios.get(API_URL + `orders_for_physician/?page=${page}`);
  }

  getAllOrders(page) {
    return axios.get(API_URL + `orders/?page=${page}`);
  }

  getProcessedOrders(page) {
    return axios.get(API_URL + `processed_orders/?page=${page}`);
  }

  getNotProcessedOrders(page) {
    return axios.get(API_URL + `not_processed_orders/?page=${page}`);
  }

  post(order) {
    return axios.post(API_URL + "create_order/", { "product_types": order });
  }
}

const orderService = new OrderService();
export default orderService;
