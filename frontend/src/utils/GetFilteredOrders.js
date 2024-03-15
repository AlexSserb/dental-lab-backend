import orderService from '../servicies/OrderService';


export default function getFilteredOrders(orderPage, filterType) {
    switch (filterType) {
        case "all": return orderService.getAllOrders(orderPage);
        case "processed": return orderService.getProcessedOrders(orderPage);
        default: return orderService.getNotProcessedOrders(orderPage);
    }
};
