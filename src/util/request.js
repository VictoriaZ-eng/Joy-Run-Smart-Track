import instance from"./instance";
export default{
    getmetro(){
        return instance({
            url:"/metro",
            method:"GET",
        });
    },
    getbus(){
        return instance({
            url:"/bus",
            method:"GET",
        });
    },
    getroute1(){
        return instance({
            url:"/route1",
            method:"GET",
        });
    },
    getroute2(){
        return instance({
            url:"/route2",
            method:"GET",
        });
    },
    getroute3(){
        return instance({
            url:"/route3",
            method:"GET",
        });
    },
    getdibiao1(){
        return instance({
            url:"/dibiao1",
            method:"GET",
        });
    },
    getdibiao2(){
        return instance({
            url:"/dibiao2",
            method:"GET",
        });
    },
    getdibiao3(){
        return instance({
            url:"/dibiao3",
            method:"GET",
        });
    },
}