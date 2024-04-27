
export function getDepartmentName(code) {
    switch (code) {
        case "MO": return "Отдел моделирования";
        case "CA": return "Информационный отдел CAD/CAM";
        case "CE": return "Отдел керамики";
        case "DE": return "Отдел протезирования";
        default: return "Код не известен";
    }
};

export function getDepartmentIdByCode(code) {
    switch (code) {
        case "MO": return 1;
        case "CA": return 2;
        case "CE": return 3;
        case "DE": return 4;
        default: return -1;
    }
};
