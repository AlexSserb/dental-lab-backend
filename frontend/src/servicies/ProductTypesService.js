import axios from "axios";

const API_URL = "api/product_types/";

class ProductTypesService {
  getAll() {
    return axios.get(API_URL);
  }
}

const productTypesService = new ProductTypesService();
export default productTypesService;
