import axios from "axios";

const API_URL = "api/products/";

class ProductService {
  getForOrder(orderId) {
    return axios.get(API_URL + orderId);
  }

  getWithOperationsForOrder(orderId) {
    return axios.get(API_URL + `operations/${orderId}`);
  }
}

const productService = new ProductService();
export default productService;
