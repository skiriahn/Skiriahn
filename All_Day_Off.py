All_Day_Off.py
# All_Day_Off.py
# 사용법 예시(단축어/URL에서 호출):
# pythonista3://add_day_off.py?action=run&argv=2025&argv=11&argv=1,5,9,10,15,16,23,24,29

import sys, time, datetime
from objc_util import ObjCClass, ObjCBlock, on_main_thread, ns, c_void_p, c_bool

# ---- EventKit 클래스들 준비
EKEventStore = ObjCClass('EKEventStore')
EKEvent = ObjCClass('EKEvent')
NSDate = ObjCClass('NSDate')

def pydate_to_ns(d: datetime.datetime):
    ts = time.mktime(d.timetuple())
    return NSDate.dateWithTimeIntervalSince1970_(ts)

@on_main_thread
def request_access(store):
    granted_box = {'value': None}
    def handler(_cmd, granted, error):
        granted_box['value'] = bool(granted)
    block = ObjCBlock(handler, restype=None, argtypes=[c_void_p, c_bool, c_void_p])
    # 0 = events
    store.requestAccessToEntityType_completion_(0, block)
    # 간단 대기 루프
    while granted_box['value'] is None:
        time.sleep(0.05)
    return granted_box['value']

@on_main_thread
def add_all_day_event(store, title, y, m, d, notes=None):
    cal = store.defaultCalendarForNewEvents()
    event = EKEvent.eventWithEventStore_(store)

    start_py = datetime.datetime(y, m, d, 0, 0, 0)
    end_py = start_py + datetime.timedelta(days=1)
    start = pydate_to_ns(start_py)
    end = pydate_to_ns(end_py)

    # 중복 방지: 같은 날 같은 제목 있으면 스킵
    pred = store.predicateForEventsWithStartDate_endDate_calendars_(start, end, None)
    exist = store.eventsMatchingPredicate_(pred)
    for e in exist:
        try:
            if str(e.title()) == title:
                # 이미 있음 → 스킵
                return False
        except Exception:
            pass

    event.setCalendar_(cal)
    event.setTitle_(title)
    event.setStartDate_(start)
    event.setEndDate_(end)
    event.setAllDay_(True)
    if notes:
        event.setNotes_(ns(notes))
    ok = store.saveEvent_span_error_(event, 0, None)
    return True

def main():
    # 인자: year month "1,5,9,10,..."
    if len(sys.argv) >= 4:
        year = int(sys.argv[1])
        month = int(sys.argv[2])
        raw = sys.argv[3]
    else:
        # 단축어 없이 직접 돌릴 때를 대비한 기본값
        year = datetime.datetime.now().year
        month = datetime.datetime.now().month
        raw = "1,5,9,10,15,16,23,24,29"

    days = [int(s.strip()) for s in raw.replace(' ', '').split(',') if s.strip()]

    store = EKEventStore.alloc().init()
    if not request_access(store):
        print("❌ 캘린더 접근 권한이 거부되었습니다. 설정 앱에서 Pythonista > 캘린더 접근 허용하세요.")
        return

    title = "Day Off"
    added, skipped = [], []
    for d in days:
        ok = add_all_day_event(store, title, year, month, d)
        (added if ok else skipped).append(d)

    print(f"✅ 추가됨: {added}" + (f" / ⏭️ 이미 존재(스킵): {skipped}" if skipped else ""))

if __name__ == "__main__":
    main()
