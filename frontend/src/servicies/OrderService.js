import axios from "axios";

const API_URL = "api/";

class OrderService {
  getOrdersForUser(accessToken) {
    return axios.get(API_URL + "orders/", {
      headers: { "Authorization": "Bearer " + String(accessToken) }
    });
  }

  post(accessToken, order) {
    return axios.post(API_URL + "create_order/", { "product_types": order }, {
      headers: { "Authorization": "Bearer " + String(accessToken) }
    });
  }
}

const orderService = new OrderService();
export default orderService;
