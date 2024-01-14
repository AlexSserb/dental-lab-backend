import axios from "axios";

const API_URL = "api/products/";

class ProductService {
  getForOrder(accessToken, order_id) {
    return axios.get(API_URL + order_id, {
      headers: { 'Authorization': 'Bearer ' + String(accessToken) }
    });
  }
}

const productService = new ProductService();
export default productService;
