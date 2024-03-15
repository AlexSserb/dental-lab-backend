
export default function getDepartmentName(code) {
    switch (code) {
        case "MO": return "Отдел моделирования";
        case "CA": return "Информационный отдел CAD/CAM";
        case "CE": return "Отдел керамики";
        case "DE": return "Отдел протезирования";
        default: return "Код не известен";
    }
};
