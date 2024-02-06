import axios from "axios";

const API_URL = "api/product_types/";

class ProductTypesService {
  getAll(accessToken) {
    return axios.get(API_URL, {
      headers: { "Authorization": "Bearer " + String(accessToken) }
    });
  }
}

const productTypesService = new ProductTypesService();
export default productTypesService;
