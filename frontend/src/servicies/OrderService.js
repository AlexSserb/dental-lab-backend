import axios from "axios";

const API_URL = "api/orders/";

class OrderService {
  getOrdersForUser(accessToken) {
    return axios.get(API_URL, {
      headers: { 'Authorization': 'Bearer ' + String(accessToken) }
    });
  }
}

const orderService = new OrderService();
export default orderService;
