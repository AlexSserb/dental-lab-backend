import React, { useState, useEffect, useContext } from 'react';
import { Form, FormGroup, Table, Label, Input, Button } from "reactstrap";
import InfoIcon from '@mui/icons-material/Info';
import { Box, Typography, Grid, TextField, Stack } from '@mui/material';
import AuthContext from '../context/AuthContext';
import orderService from '../servicies/OrderService';
import { useNavigate } from 'react-router-dom';
import productService from '../servicies/ProductService';
import ToothMarks from './ToothMarks';


const PhysicianOrderList = () => {
  let { user, authTokens, userGroupToString } = useContext(AuthContext);
  const [userGroup, setUserGroup] = useState(userGroupToString());
  const [orders, setOrders] = useState([]);
  const [products, setProducts] = useState([]);
  const [currOrder, setCurrOrder] = useState({});
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
        <td className="text-nowrap">{order.order_date}</td>
        <td>{order.status.name}</td>
        <td className="text-center">
          <Button onClick={() => getOrderInfo(order)}>
            <InfoIcon />
          </Button>
        </td>
      </tr>
    ));
  };

  const renderProducts = () => {
    let i = 1;
    return products.map(product => (
      <tr key={product.id}>
        <td>{i++}</td>
        <td>{product.product_type.name}</td>
        <td>{product.product_status.name}</td>
        <td>{product.amount}</td>
        <td><ToothMarks teethList={product.teeth.map(tooth => tooth.tooth_number)} /></td>
      </tr>
    ));
  }

  return (
    <Grid container spacing={3} >
      <Grid item xs={4}>
        <h3 className='m-4 mt-5'>Заказы</h3>
        <Button className="mx-4" color="primary" onClick={() => { navigate("/create_order") }}>Оформить заказ</Button>
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
                    {renderOrders()}
                  </tbody>
                </Table>
              </div>
              : <div className="mt-3">Нет заказов</div>
          }
        </div>
      </Grid>
      <Grid item xs={8}>
        <Box sx={{
          border: 1,
          borderRadius: 2,
          borderColor: '#4d4c4c',
          padding: 3,
          marginTop: 5,
        }}>
          <Typography textAlign={"center"} variant="h4" component="h4">
            Информация о заказе
          </Typography>
          <Box>
            <Stack spacing={2}>
              {
                products.length > 0 ?
                  <>
                    <Table label='Изделия'>
                      <thead>
                        <tr>
                          <th>№</th>
                          <th>Тип изделия</th>
                          <th>Статус</th>
                          <th style={{width: "8%"}}>Кол-во</th>
                          <th>Отметки</th>
                        </tr>
                      </thead>
                      <tbody>
                        {renderProducts()}
                      </tbody>
                    </Table>
                  </>
                  : <Label for="products">Изделия для заказа</Label>
              }
              <TextField
                InputProps={{
                  readOnly: true,
                }}
                InputLabelProps={{ shrink: currOrder?.status?.name }}
                label="Статус"
                variant="outlined"
                value={currOrder?.status?.name}
              />
              <TextField
                InputProps={{
                  readOnly: true,
                }}
                InputLabelProps={{ shrink: "TODO" }}
                label="Стоимость заказа"
                variant="outlined"
                value="TODO"
              />
              <TextField
                InputProps={{
                  readOnly: true,
                }}
                InputLabelProps={{ shrink: currOrder?.order_date }}
                label="Дата"
                variant="outlined"
                value={currOrder?.order_date}
              />
            </Stack>
          </Box>
        </Box>
      </Grid>
    </Grid>
  )
}

export default PhysicianOrderList;