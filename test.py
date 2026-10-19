with app.app_context():
    from models import db, AdmissionItem, Admission
    q = db.session.query(
        AdmissionItem.service_code, 
        AdmissionItem.service_name, 
        db.func.sum(AdmissionItem.count).label('count')
    ).join(Admission).filter(Admission.admission_date >= '1405/01/01', Admission.admission_date <= '1405/12/30')
    items = q.group_by(AdmissionItem.service_code).all()
    print("تعداد:", len(items))
    for i in items:
        print(i)