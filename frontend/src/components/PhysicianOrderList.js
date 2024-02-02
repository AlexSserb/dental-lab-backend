import React, { useState, useEffect, useContext } from 'react';
import InfoIcon from '@mui/icons-material/Info';
import { 
  Box, 
  Typography, 
  Grid, 
  TextField, 
  Stack, 
  Table, TableContainer, TableHead, TableBody, TableRow, TableCell,
  Button,
  Paper
} from '@mui/material';
import AuthContext from '../context/AuthContext';
import orderService from '../servicies/OrderService';
import { useNavigate } from 'react-router-dom';
import productService from '../servicies/ProductService';
import ToothMarks from './ToothMarks';


const PhysicianOrderList = () => {
  const { authTokens, userGroupToString } = useContext(AuthContext);
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
      <TableRow key={order.id}>
        <TableCell>{i++}</TableCell>
        <TableCell sx={{textWrap: "nowrap"}}>{order.order_date}</TableCell>
        <TableCell>{order.status.name}</TableCell>
        <TableCell sx={{textAlign: "center"}}>
          <Button onClick={() => getOrderInfo(order)}>
            <InfoIcon />
          </Button>
        </TableCell>
      </TableRow>
    ));
  };

  const renderProducts = () => {
    let i = 1;
    return products.map(product => (
      <TableRow key={product.id}>
        <TableCell>{i++}</TableCell>
        <TableCell>{product.product_type.name}</TableCell>
        <TableCell>{product.product_status.name}</TableCell>
        <TableCell>{product.amount}</TableCell>
        <TableCell><ToothMarks teethList={product.teeth.map(tooth => tooth.tooth_number)} /></TableCell>
      </TableRow>
    ));
  }

  return (
    <Grid container spacing={3} wrap="wrap-reverse">
      <Grid item xs={4}>
        <h3 className='m-4 mt-5'>Заказы</h3>
        <Button variant="contained" onClick={() => { navigate("/create_order") }}
          sx={{
            margin: "15px"
          }}>
          Оформить заказ
        </Button>
        {
          orders.length > 0 ?
          <TableContainer component={Paper}>
            <Table>
              <TableHead>
                <TableRow>
                  <TableCell>№</TableCell>
                  <TableCell>Дата</TableCell>
                  <TableCell>Статус</TableCell>
                  <TableCell></TableCell>
                </TableRow>
              </TableHead>
              <TableBody>
                {renderOrders()}
              </TableBody>
            </Table>
            </TableContainer>
            : <div className="mt-3">Нет заказов</div>
        }
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
                  <TableContainer component={Paper}>
                    <Table label='Изделия'>
                      <TableHead>
                        <TableRow>
                          <TableCell>№</TableCell>
                          <TableCell>Тип изделия</TableCell>
                          <TableCell>Статус</TableCell>
                          <TableCell style={{ width: "8%" }}>Кол-во</TableCell>
                          <TableCell>Отметки</TableCell>
                        </TableRow>
                      </TableHead>
                      <TableBody>
                        {renderProducts()}
                      </TableBody>
                    </Table>
                  </TableContainer>
                  : <p for="products">Изделия для заказа</p>
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