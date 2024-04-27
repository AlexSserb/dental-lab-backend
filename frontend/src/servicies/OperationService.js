import axios from "axios";
import dayjs from "dayjs";

const API_URL = "api/";

class OperationService {
  timeZone = dayjs?.tz?.guess();

  getForTech(page) {
    return axios.get(API_URL + `operations-for-tech/?page=${page}`);
  }

  getForProduct(productId) {
    return axios.get(API_URL + `operations-for-product/${productId}`);
  }

  getForSchedule(userEmail, date) {
    return axios.get(API_URL + `operations-for-schedule/${userEmail}/${date}`);
  }

  setOperationExecStart(operationId, datetime) {
    return axios.patch(API_URL + `operation-exec-start/${operationId}/${datetime}`);
  }

  getOperationStatuses() {
    return axios.get(API_URL + "operation-statuses/");
  }

  setOperationStatus(operationId, statusId) {
    return axios.patch(API_URL + `operation/${operationId}/`, { statusId: statusId });
  }

  assignOperation(operation) {
    operation.execStart = dayjs.utc(operation?.execStart).tz(this.timeZone);

    return axios.patch(API_URL + 'assign-operation/', {
      id: operation?.id,
      execStart: dayjs(operation?.execStart),
      techEmail: operation?.tech?.email
    });
  }
}

const operationService = new OperationService();
export default operationService;
