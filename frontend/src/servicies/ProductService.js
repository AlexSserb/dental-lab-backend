import axios from "axios";

const API_URL = "api/products/";

class ProductService {
  getForOrder(order_id) {
    return axios.get(API_URL + order_id);
  }
}

const productService = new ProductService();
export default productService;
