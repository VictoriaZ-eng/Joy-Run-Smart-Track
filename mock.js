//require是commonjs规范 在后端接口还没开发完成时，用模拟的数据（JSON 格式为主）来模拟接口返回结果
// npm run mock
const mockjs=require("mockjs");
const metro=require("./src/GIS-data/地铁站.json");
const bus=require("./src/GIS-data/公交站.json");
const route1=require("./src/GIS-data/推荐路线2/01.json")
const route2=require("./src/GIS-data/推荐路线2/02.json")
const route3=require("./src/GIS-data/推荐路线2/03.json")
const dibiao1=require("./src/GIS-data/推荐路线2/01地标1.json")
const dibiao2=require("./src/GIS-data/推荐路线2/02地标1.json")
const dibiao3=require("./src/GIS-data/推荐路线2/03地标1.json")
module.exports=()=>{
    return mockjs.mock({
        metro,
        bus,
        route1,
        route2,
        route3,
        dibiao1,
        dibiao2,
        dibiao3,
    });
};