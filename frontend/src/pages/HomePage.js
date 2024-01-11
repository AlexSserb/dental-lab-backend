import React, { useState, useEffect, useContext } from 'react';
import { Form, Table } from "reactstrap";

import AuthContext from '../context/AuthContext';
import orderService from '../servicies/OrderService';
import { useNavigate } from 'react-router-dom';

const HomePage = () => {
  let { user, authTokens, userGroupToString } = useContext(AuthContext);
  const [ userGroup, setUserGroup ] = useState(userGroupToString());
  const [ orders, setOrders ] = useState([]);
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

  // Main variable to render items on the screen
  const renderItems = () => {
    let i = 1;
    return orders.map((order) => (
      <tr key={order.id}> 
        <td>{i++}</td>
				<td>{order.order_date}</td>
				<td>{order.status.name}</td>
    	</tr>
  	));
  };

  return (
    <div>
      { userGroup === "Врач" ? (
        <>
          <h3 className='p-4'>Заказы</h3>
          <div className='col-md-5 px-4'>
            { 
              orders.length > 0 ? 
              <div className='row'>
                <Table className="mt-4" striped> 
                  <thead> 
                    <tr> 
                      <th>№</th>
                      <th>Дата</th> 
                      <th>Статус</th>
                    </tr> 
                  </thead> 
                  <tbody> 
                    {renderItems()}
                  </tbody> 
                </Table> 
              </div>
              : <div className="mt-3">Нет заказов</div>
            }
            <Form>

            </Form>
          </div>
        </>
      ) : (
        <></>
      )}
    </div>
  )
}

export default HomePage;
