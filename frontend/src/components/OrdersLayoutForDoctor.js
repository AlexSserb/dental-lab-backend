import React, { useState, useEffect, useContext } from 'react';
import { Form, FormGroup, Table, Label, Input, Button } from "reactstrap";
import InfoIcon from '@mui/icons-material/Info';

import AuthContext from '../context/AuthContext';
import orderService from '../servicies/OrderService';
import { useNavigate } from 'react-router-dom';
import productService from '../servicies/ProductService';
import ToothMarks from './ToothMarks';


const OrdersLayoutForDoctor = () => {
  let { user, authTokens, userGroupToString } = useContext(AuthContext);
  const [ userGroup, setUserGroup ] = useState(userGroupToString());
  const [ orders, setOrders ] = useState([]);
  const [ products, setProducts ] = useState([]);
  const [ currOrder, setCurrOrder ] = useState({});
  const navigate = useNavigate();

  useEffect(() => {
    if (!authTokens || !authTokens.access) {
      navigate('/login');
      return;
    }
    if (userGroup === "Врач") {
      orderService.getOrdersForUser(authTokens.access)
        .then(res => {
          setOrders(res.data);
        })
        .catch(err => {
          console.log(err);
        });
    }
  }, []);

  const getOrderInfo = (order) => {
    productService.getForOrder(authTokens.access, order.id)
      .then(res => {
        setProducts(res.data);
        setCurrOrder(order);
      })
      .catch(err => {
        setProducts([]);
        setCurrOrder({});
        console.log(err);
      });
  }

  // Main variable to render orders on the screen
  const renderOrders = () => {
    let i = 1;
    return orders.map((order) => (
      <tr key={order.id}> 
        <td>{i++}</td>
				<td>{order.order_date}</td>
				<td>{order.status.name}</td>
        <td className="text-center">
          <Button onClick={() => getOrderInfo(order)}>
            <InfoIcon/>
          </Button>
        </td>
    	</tr>
  	));
  };

  const renderProducts = () => {
    let i = 1;
    return products.map((product) => (
      <tr key={product.id}> 
        <td>{i++}</td>
				<td>{product.product_type.name}</td>
				<td>{product.product_status.name}</td>
        <td>{product.amount}</td>
        <td><ToothMarks teethList={product.teeth}/></td>
    	</tr>
  	));
  }

  return (
    <div style={{display: 'flex'}}>
      <div>
        <h3 className='p-4 pt-5'>Заказы</h3> 
        <div className='col-md-50 px-4'>
        { 
          orders.length > 0 ? 
          <div>
            <Table className="mt-4"> 
              <thead> 
                <tr> 
                  <th>№</th>
                  <th>Дата</th> 
                  <th>Статус</th>
                  <th></th>
                </tr> 
              </thead> 
              <tbody> 
                { renderOrders() }
              </tbody> 
            </Table> 
          </div>
          : <div className="mt-3">Нет заказов</div>
        }
        </div>
      </div>
      <div className="card card-container col-sm-70 mx-auto px-3 mt-5">
        <h4 className="text-success text-uppercase text-center mt-4">
          Информация о заказе
        </h4> 
        <div className='m-4'>
          <Form display>
            <FormGroup>
              {
                products.length > 0 ? 
                <>
                  <Label for="products">Изделия</Label>
                  <Table bordered> 
                    <thead> 
                      <tr> 
                        <th>№</th>
                        <th>Тип изделия</th> 
                        <th>Статус</th>
                        <th>Количество</th>
                        <th>Отметки</th>
                      </tr> 
                    </thead> 
                    <tbody> 
                      { renderProducts() }
                    </tbody> 
                  </Table> 
                </>
                : <Label for="products">Изделия для заказа</Label>
              }
            </FormGroup>
            <FormGroup>
              <Label for="cost">Статус</Label>
              <Input type="text" value={currOrder?.status?.name} disabled/>
            </FormGroup>
            <FormGroup>
              <Label for="cost">Цена за заказ</Label>
              <Input
                type="number" min="1" step="any"
                name="password" value="TODO" disabled
              />
            </FormGroup>
            <FormGroup>
              <Label for="cost">Дата</Label>
              <Input type="text" value={currOrder?.order_date} disabled/>
            </FormGroup>
          </Form>
        </div>
      </div>
    </div>
  )
}

export default OrdersLayoutForDoctor;
