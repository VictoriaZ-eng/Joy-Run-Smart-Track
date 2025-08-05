import axios from "axios";
const instance=axios.create({
    baseURL:"http://localhost:8080",
});
instance.interceptors.response.use(
    function(response){
        if (response.status===200){
            return response.data;
        }else{
            return Promise.reject(response.data);
        }
    },
    function(error){
        return Promise.reject(error);
    }
);
export default instance;