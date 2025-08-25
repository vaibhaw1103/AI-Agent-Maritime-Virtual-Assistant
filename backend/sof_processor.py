#!/usr/bin/env python3
"""
🚢 MARITIME ASSISTANT - STATEMENT OF FACTS (SOF) PROCESSOR
==========================================================

Advanced SOF document processing with:
- Template-agnostic event extraction
- Time parsing with multiple formats
- Low confidence data flagging for user editing
- Structured export (JSON/CSV)
- Comprehensive event detection

Version: 1.0
Date: August 22, 2025
"""

import re
import json
import csv
from datetime import datetime, timedelta
from typing import Dict, List, Any, Optional, Tuple
import logging
from dataclasses import dataclass, asdict
from io import StringIO

logger = logging.getLogger(__name__)

@dataclass
class SoFEvent:
    """Structure for a Statement of Facts event"""
    event_type: str
    description: str
    start_time: Optional[datetime] = None
    end_time: Optional[datetime] = None
    start_time_str: str = ""
    end_time_str: str = ""
    confidence: float = 0.0
    extracted_text: str = ""
    vessel: str = ""
    port: str = ""
    duration_hours: Optional[float] = None

@dataclass
class SoFDocument:
    """Complete Statement of Facts document structure"""
    vessel_name: str = ""
    imo_number: str = ""
    voyage_number: str = ""
    port: str = ""
    berth: str = ""
    events: List[SoFEvent] = None
    total_laytime: Optional[float] = None
    demurrage_time: Optional[float] = None
    despatch_time: Optional[float] = None
    document_confidence: float = 0.0
    stops: List[Any] = None
    
    def __post_init__(self):
        if self.events is None:
            self.events = []
        if self.stops is None:
            self.stops = []

class StatementOfFactsProcessor:
    """Advanced SOF document processor"""
    
    # Common SOF event patterns (template-agnostic)
    EVENT_PATTERNS = {
        'nor_tendered': [
            r'n\.?o\.?r\.?\s+(?:tender(?:ed)?|given)',
            r'notice\s+of\s+readiness\s+(?:tender(?:ed)?|given)',
            r'nor\s+(?:at|on)\s+(?:\d{2}:\d{2}|\d{4})',
            r'tendered?\s+n\.?o\.?r\.?'
        ],
        'nor_accepted': [
            r'n\.?o\.?r\.?\s+(?:accept(?:ed)?|confirmed)',
            r'notice\s+of\s+readiness\s+(?:accept(?:ed)?|confirmed)',
            r'accepted?\s+n\.?o\.?r\.?'
        ],
        'berthing_commence': [
            r'(?:commenced?|start(?:ed)?|began)\s+(?:berth(?:ing)?|alongside)',
            r'(?:berth(?:ing)?|alongside)\s+(?:commenced?|start(?:ed)?)',
            r'vessel\s+alongside',
            r'(?:made\s+fast|all\s+fast)',
            r'berth(?:ing)?\s+complet(?:e|ed)'
        ],
        'loading_commence': [
            r'(?:commenced?|start(?:ed)?|began)\s+(?:load(?:ing)?|cargo\s+ops?)',
            r'(?:load(?:ing)?|cargo)\s+(?:operations?\s+)?(?:commenced?|start(?:ed)?)',
            r'first\s+(?:crane|gear|hatch)',
            r'(?:hoses?\s+)?connect(?:ed)?'
        ],
        'loading_complete': [
            r'(?:complet(?:ed)?|finish(?:ed)?|end(?:ed)?)\s+(?:load(?:ing)?|cargo\s+ops?)',
            r'(?:load(?:ing)?|cargo)\s+(?:operations?\s+)?(?:complet(?:ed)?|finish(?:ed)?)',
            r'last\s+(?:crane|gear|hatch)',
            r'(?:hoses?\s+)?disconnect(?:ed)?',
            r'all\s+cargo\s+(?:on\s+board|loaded)'
        ],
        'discharging_commence': [
            r'(?:commenced?|start(?:ed)?|began)\s+(?:discharg(?:ing)?|unload(?:ing)?)',
            r'(?:discharg(?:ing)?|unload(?:ing)?)\s+(?:operations?\s+)?(?:commenced?|start(?:ed)?)',
            r'first\s+(?:crane|gear|hatch)\s+(?:discharg(?:ing)?|unload(?:ing)?)'
        ],
        'discharging_complete': [
            r'(?:complet(?:ed)?|finish(?:ed)?|end(?:ed)?)\s+(?:discharg(?:ing)?|unload(?:ing)?)',
            r'(?:discharg(?:ing)?|unload(?:ing)?)\s+(?:operations?\s+)?(?:complet(?:ed)?|finish(?:ed)?)',
            r'last\s+(?:crane|gear|hatch)\s+(?:discharg(?:ing)?|unload(?:ing)?)',
            r'all\s+cargo\s+(?:discharged?|unloaded?)'
        ],
        'unberthing_commence': [
            r'(?:commenced?|start(?:ed)?|began)\s+(?:unberth(?:ing)?|cast(?:ing)?\s+off)',
            r'(?:unberth(?:ing)?|cast\s+off)\s+(?:commenced?|start(?:ed)?)',
            r'let\s+go\s+(?:all\s+)?(?:lines?|ropes?)',
            r'(?:cast|let)\s+off'
        ],
        'departure': [
            r'(?:departed?|left|sailed?)\s+(?:berth|port|anchorage)',
            r'vessel\s+(?:departed?|left|sailed?)',
            r'(?:finished\s+with\s+engines?|f\.?w\.?e\.?)',
            r'(?:pilot\s+)?disembark(?:ed)?'
        ],
        'weather_delay': [
            r'weather\s+(?:delay|stop(?:page)?|interrupt(?:ion)?)',
            r'(?:delay|stop(?:page)?)\s+(?:due\s+to\s+)?weather',
            r'(?:rain|wind|storm|fog)\s+(?:delay|stop(?:page)?)',
            r'(?:suspended?|halt(?:ed)?)\s+(?:due\s+to\s+)?(?:weather|rain|wind)'
        ],
        'mechanical_delay': [
            r'(?:mechanical|equipment|crane|gear)\s+(?:delay|breakdown|failure)',
            r'(?:delay|breakdown|failure)\s+(?:of\s+)?(?:mechanical|equipment|crane|gear)',
            r'(?:suspended?|halt(?:ed)?)\s+(?:due\s+to\s+)?(?:mechanical|breakdown)'
        ],
        'waiting_berth': [
            r'wait(?:ing)?\s+(?:for\s+)?berth',
            r'berth\s+(?:not\s+)?(?:available|ready)',
            r'(?:delay|wait(?:ing)?)\s+(?:for\s+)?(?:berth|alongside)'
        ],
        'waiting_cargo': [
            r'wait(?:ing)?\s+(?:for\s+)?cargo',
            r'cargo\s+(?:not\s+)?(?:available|ready)',
            r'(?:delay|wait(?:ing)?)\s+(?:for\s+)?cargo'
        ]
    }
    
    # Time format patterns
    TIME_PATTERNS = [
        r'\b(\d{1,2}):(\d{2})\s*(?:hrs?|hours?)?\s*(?:on\s+)?(\d{1,2})[\/\-\.](\d{1,2})[\/\-\.](\d{2,4})\b',
        r'\b(\d{4})\s*(?:hrs?|hours?)?\s*(?:on\s+)?(\d{1,2})[\/\-\.](\d{1,2})[\/\-\.](\d{2,4})\b',
        r'\b(\d{1,2}):(\d{2})\s*(?:on\s+)?(\d{1,2})(?:st|nd|rd|th)?\s+(\w+)\s+(\d{2,4})\b',
        r'\b(\d{4})\s*(?:hrs?|hours?)?\s*(?:on\s+)?(\d{1,2})(?:st|nd|rd|th)?\s+(\w+)\s+(\d{2,4})\b'
    ]
    
    # Month name mapping
    MONTHS = {
        'january': 1, 'jan': 1, 'february': 2, 'feb': 2, 'march': 3, 'mar': 3,
        'april': 4, 'apr': 4, 'may': 5, 'june': 6, 'jun': 6, 'july': 7, 'jul': 7,
        'august': 8, 'aug': 8, 'september': 9, 'sep': 9, 'october': 10, 'oct': 10,
        'november': 11, 'nov': 11, 'december': 12, 'dec': 12
    }
    
    @staticmethod
    def extract_vessel_info(text: str) -> Dict[str, str]:
        """Extract vessel name and IMO number"""
        vessel_info = {"vessel_name": "", "imo_number": "", "voyage_number": ""}
        
        # Vessel name patterns
        vessel_patterns = [
            r'(?:m\.?v\.?|s\.?s\.?|vessel)\s+([A-Z\s\-\d]+)',
            r'vessel\s*:\s*([A-Z\s\-\d]+)',
            r'name\s*:\s*([A-Z\s\-\d]+)'
        ]
        
        for pattern in vessel_patterns:
            match = re.search(pattern, text, re.IGNORECASE)
            if match:
                vessel_info["vessel_name"] = match.group(1).strip()
                break
        
        # IMO number
        imo_match = re.search(r'imo\s*:?\s*(\d{7})', text, re.IGNORECASE)
        if imo_match:
            vessel_info["imo_number"] = imo_match.group(1)
        
        # Voyage number
        voyage_match = re.search(r'voyage\s*:?\s*([A-Z\d\-]+)', text, re.IGNORECASE)
        if voyage_match:
            vessel_info["voyage_number"] = voyage_match.group(1)
        
        return vessel_info
    
    @staticmethod
    def extract_port_info(text: str) -> Dict[str, str]:
        """Extract port and berth information"""
        port_info = {"port": "", "berth": ""}
        
        # Port patterns
        port_patterns = [
            r'port\s*:?\s*([A-Z\s\-]+)',
            r'(?:at\s+)?(?:port\s+of\s+)?([A-Z\s\-]+)(?:\s+port)?',
            r'berth\s*:?\s*([A-Z\d\s\-]+)'
        ]
        
        for pattern in port_patterns:
            match = re.search(pattern, text, re.IGNORECASE)
            if match:
                port_name = match.group(1).strip()
                if len(port_name) > 3 and not port_name.lower() in ['the', 'and', 'for', 'with']:
                    port_info["port"] = port_name
                    break
        
        # Berth information
        berth_match = re.search(r'berth\s*:?\s*([A-Z\d\s\-]+)', text, re.IGNORECASE)
        if berth_match:
            port_info["berth"] = berth_match.group(1).strip()
        
        return port_info
    
    @staticmethod
    def parse_time(time_str: str, context_text: str = "") -> Tuple[Optional[datetime], float]:
        """Parse various time formats with confidence scoring"""
        time_str = time_str.strip()
        confidence = 0.0
        
        for pattern in StatementOfFactsProcessor.TIME_PATTERNS:
            match = re.search(pattern, time_str, re.IGNORECASE)
            if match:
                try:
                    groups = match.groups()
                    
                    # Pattern 1: HH:MM on DD/MM/YYYY
                    if len(groups) == 5 and ':' in groups[0]:
                        hour, minute, day, month, year = groups
                        hour, minute = int(hour), int(minute)
                        day, month, year = int(day), int(month), int(year)
                        confidence = 0.9
                    
                    # Pattern 2: HHMM on DD/MM/YYYY
                    elif len(groups) == 4 and len(groups[0]) == 4:
                        time_val, day, month, year = groups
                        hour = int(time_val[:2])
                        minute = int(time_val[2:])
                        day, month, year = int(day), int(month), int(year)
                        confidence = 0.85
                    
                    # Pattern 3: HH:MM on DDth Month YYYY
                    elif len(groups) == 5 and ':' in groups[0]:
                        hour, minute, day, month_name, year = groups
                        hour, minute = int(hour), int(minute)
                        day, year = int(day), int(year)
                        month = StatementOfFactsProcessor.MONTHS.get(month_name.lower(), 1)
                        confidence = 0.9
                    
                    # Pattern 4: HHMM on DDth Month YYYY
                    elif len(groups) == 4 and len(groups[0]) == 4:
                        time_val, day, month_name, year = groups
                        hour = int(time_val[:2])
                        minute = int(time_val[2:])
                        day, year = int(day), int(year)
                        month = StatementOfFactsProcessor.MONTHS.get(month_name.lower(), 1)
                        confidence = 0.85
                    
                    else:
                        continue
                    
                    # Adjust year format
                    if year < 50:
                        year += 2000
                    elif year < 100:
                        year += 1900
                    
                    parsed_time = datetime(year, month, day, hour, minute)
                    return parsed_time, confidence
                    
                except (ValueError, IndexError) as e:
                    logger.warning(f"Time parsing error: {e}")
                    continue
        
        return None, 0.0

    @staticmethod
    def _parse_time_only(time_only_str: str) -> Tuple[Optional[datetime], float]:
        """Parse time strings without date context by assuming nearest reasonable date.
        Best-effort: return a datetime on today's date with given hour/minute.
        """
        try:
            m = re.match(r"(\d{1,2}):(\d{2})", time_only_str)
            if not m:
                return None, 0.0
            hour = int(m.group(1)); minute = int(m.group(2))
            now = datetime.now()
            parsed = datetime(now.year, now.month, now.day, hour, minute)
            return parsed, 0.6
        except Exception:
            return None, 0.0
    
    @staticmethod
    def extract_events(text: str) -> List[SoFEvent]:
        """Extract all events from SOF text with confidence scoring"""
        events = []
        lines = text.split('\n')
        
        vessel_info = StatementOfFactsProcessor.extract_vessel_info(text)
        port_info = StatementOfFactsProcessor.extract_port_info(text)
        
        for i, line in enumerate(lines):
            line = line.strip()
            if not line:
                continue
            
            # Check each event type
            for event_type, patterns in StatementOfFactsProcessor.EVENT_PATTERNS.items():
                for pattern in patterns:
                    if re.search(pattern, line, re.IGNORECASE):
                        # Try to extract inline time ranges first (start and end on same line)
                        start_time, end_time = None, None
                        time_confidence = 0.0

                        # Detect inline ranges like '12:00 - 14:30' or '1200-1430'
                        range_match = re.search(r"(\d{1,2}:\d{2}|\d{3,4})\s*(?:-|to)\s*(\d{1,2}:\d{2}|\d{3,4})", line)
                        if range_match:
                            s_raw, e_raw = range_match.group(1), range_match.group(2)
                            parsed_s, conf_s = StatementOfFactsProcessor.parse_time(s_raw, line)
                            parsed_e, conf_e = StatementOfFactsProcessor.parse_time(e_raw, line)
                            if not parsed_s:
                                parsed_s, conf_s = StatementOfFactsProcessor._parse_time_only(s_raw)
                            if not parsed_e:
                                parsed_e, conf_e = StatementOfFactsProcessor._parse_time_only(e_raw)
                            start_time, end_time = parsed_s, parsed_e
                            time_confidence = max(conf_s, conf_e)

                        # If no inline range found, parse single time in the line as start_time
                        if not start_time:
                            start_time, time_confidence = StatementOfFactsProcessor.parse_time(line)
                        
                        # Calculate overall confidence
                        pattern_confidence = 0.8 if len(patterns) <= 3 else 0.7
                        overall_confidence = min(time_confidence * pattern_confidence, 0.95)
                        
                        event = SoFEvent(
                            event_type=event_type.replace('_', ' ').title(),
                            description=line,
                            start_time=start_time,
                            end_time=end_time,
                            start_time_str=start_time.strftime('%d/%m/%Y %H:%M') if start_time else "",
                            end_time_str=end_time.strftime('%d/%m/%Y %H:%M') if end_time else "",
                            confidence=overall_confidence,
                            extracted_text=line,
                            vessel=vessel_info.get("vessel_name", ""),
                            port=port_info.get("port", "")
                        )
                        
                        events.append(event)
                        break
        
        return events
    
    @staticmethod
    def calculate_laytime_analysis(events: List[SoFEvent]) -> Dict[str, Any]:
        """Calculate laytime, demurrage and despatch from events"""
        analysis = {
            "total_laytime_hours": 0.0,
            "demurrage_hours": 0.0,
            "despatch_hours": 0.0,
            "berth_time_hours": 0.0,
            "loading_time_hours": 0.0,
            "discharging_time_hours": 0.0,
            "analysis_confidence": 0.0
        }
        
        # Find key events
        nor_tendered = None
        berth_start = None
        loading_start = None
        loading_end = None
        discharge_start = None
        discharge_end = None
        departure = None
        
        for event in events:
            if event.start_time:
                if 'nor tendered' in event.event_type.lower():
                    nor_tendered = event.start_time
                elif 'berthing commence' in event.event_type.lower():
                    berth_start = event.start_time
                elif 'loading commence' in event.event_type.lower():
                    loading_start = event.start_time
                elif 'loading complete' in event.event_type.lower():
                    loading_end = event.start_time
                elif 'discharging commence' in event.event_type.lower():
                    discharge_start = event.start_time
                elif 'discharging complete' in event.event_type.lower():
                    discharge_end = event.start_time
                elif 'departure' in event.event_type.lower():
                    departure = event.start_time
        
        # Calculate durations
        if loading_start and loading_end:
            loading_time = (loading_end - loading_start).total_seconds() / 3600
            analysis["loading_time_hours"] = loading_time
        
        if discharge_start and discharge_end:
            discharge_time = (discharge_end - discharge_start).total_seconds() / 3600
            analysis["discharging_time_hours"] = discharge_time
        
        if berth_start and departure:
            berth_time = (departure - berth_start).total_seconds() / 3600
            analysis["berth_time_hours"] = berth_time
        
        if nor_tendered and departure:
            total_time = (departure - nor_tendered).total_seconds() / 3600
            analysis["total_laytime_hours"] = total_time
        
        # Set confidence based on available data
        confidence_factors = [
            1.0 if nor_tendered else 0.0,
            1.0 if berth_start else 0.0,
            1.0 if loading_start or discharge_start else 0.0,
            1.0 if loading_end or discharge_end else 0.0,
            1.0 if departure else 0.0
        ]
        analysis["analysis_confidence"] = sum(confidence_factors) / len(confidence_factors)
        
        return analysis

    @staticmethod
    def group_port_stops(events: List[SoFEvent]) -> List[Dict[str, Any]]:
        """Group events into port stops and return a serializable list of stops."""
        stops = []
        # Use events with start_time sorted
        timed = [e for e in events if e.start_time]
        timed.sort(key=lambda e: e.start_time)

        i = 0
        n = len(timed)
        while i < n:
            e = timed[i]
            et = e.event_type.lower()

            if any(k in et for k in ['nor tendered', 'nor', 'berthing', 'berth', 'made fast', 'vessel alongside']):
                start = e.start_time
                # find next departure-like event
                end = None
                j = i + 1
                events_in_stop = [e]
                while j < n:
                    ej = timed[j]
                    events_in_stop.append(ej)
                    if any(k in ej.event_type.lower() for k in ['departure', 'unberthing', 'cast off', 'left', 'sailed']):
                        end = ej.start_time
                        break
                    j += 1

                if not end:
                    # fallback: use last event time in stop
                    end = events_in_stop[-1].start_time if events_in_stop else start

                duration = None
                try:
                    duration = (end - start).total_seconds() / 3600 if start and end else None
                except Exception:
                    duration = None

                types = {ev.event_type.lower() for ev in events_in_stop}
                stop_type = 'Berth Stay'
                if any('loading' in t for t in types) and any('discharging' in t for t in types):
                    stop_type = 'Cargo operations (Mixed)'
                elif any('loading' in t for t in types):
                    stop_type = 'Loading'
                elif any('discharging' in t for t in types):
                    stop_type = 'Discharging'
                elif any('wait' in t for t in types):
                    stop_type = 'Waiting'
                elif any('delay' in t or 'suspend' in t for t in types):
                    stop_type = 'Delayed'

                avg_conf = sum(ev.confidence for ev in events_in_stop if ev.confidence) / len([ev for ev in events_in_stop if ev.confidence]) if events_in_stop else 0.0

                stops.append({
                    'start_time': start.isoformat() if start else None,
                    'end_time': end.isoformat() if end else None,
                    'start_time_str': start.strftime('%d/%m/%Y %H:%M') if start else '',
                    'end_time_str': end.strftime('%d/%m/%Y %H:%M') if end else '',
                    'duration_hours': duration,
                    'stop_type': stop_type,
                    'confidence': avg_conf,
                    'events': [{'event_type': ev.event_type, 'description': ev.description, 'time': ev.start_time_str, 'confidence': ev.confidence} for ev in events_in_stop]
                })

                # mark duration on events where possible
                for ev in events_in_stop:
                    if ev.start_time and ev.end_time:
                        try:
                            ev.duration_hours = (ev.end_time - ev.start_time).total_seconds() / 3600
                        except Exception:
                            ev.duration_hours = None

                # move index to j+1
                i = j + 1
                continue

            i += 1

        return stops
    
    @staticmethod
    def process_sof_document(text: str) -> SoFDocument:
        """Process complete SOF document and return structured data"""
        vessel_info = StatementOfFactsProcessor.extract_vessel_info(text)
        port_info = StatementOfFactsProcessor.extract_port_info(text)
        events = StatementOfFactsProcessor.extract_events(text)
        laytime_analysis = StatementOfFactsProcessor.calculate_laytime_analysis(events)
        
        # Calculate overall document confidence
        event_confidences = [e.confidence for e in events if e.confidence > 0]
        doc_confidence = sum(event_confidences) / len(event_confidences) if event_confidences else 0.0
        
        sof_doc = SoFDocument(
            vessel_name=vessel_info.get("vessel_name", ""),
            imo_number=vessel_info.get("imo_number", ""),
            voyage_number=vessel_info.get("voyage_number", ""),
            port=port_info.get("port", ""),
            berth=port_info.get("berth", ""),
            events=events,
            total_laytime=laytime_analysis.get("total_laytime_hours"),
            document_confidence=doc_confidence
        )
        # Group events into port stops and attach
        try:
            sof_doc.stops = StatementOfFactsProcessor.group_port_stops(events)
        except Exception as e:
            logger.warning(f"Failed to group port stops: {e}")
        
        return sof_doc
    
    @staticmethod
    def export_to_json(sof_doc: SoFDocument) -> str:
        """Export SOF document to JSON format"""
        # Convert to dict with datetime serialization
        data = asdict(sof_doc)
        
        # Convert datetime objects to strings
        for event in data.get('events', []):
            if event.get('start_time'):
                event['start_time'] = event['start_time'].isoformat() if hasattr(event['start_time'], 'isoformat') else str(event['start_time'])
            if event.get('end_time'):
                event['end_time'] = event['end_time'].isoformat() if hasattr(event['end_time'], 'isoformat') else str(event['end_time'])
        
        return json.dumps(data, indent=2, default=str)
    
    @staticmethod
    def export_to_csv(sof_doc: SoFDocument) -> str:
        """Export SOF events to CSV format"""
        output = StringIO()
        writer = csv.writer(output)
        
        # Write headers
        headers = [
            'Event Type', 'Description', 'Start Time', 'End Time', 
            'Confidence', 'Vessel', 'Port', 'Duration (Hours)'
        ]
        writer.writerow(headers)
        
        # Write events
        for event in sof_doc.events:
            row = [
                event.event_type,
                event.description,
                event.start_time_str,
                event.end_time_str,
                f"{event.confidence:.2f}",
                event.vessel,
                event.port,
                event.duration_hours if event.duration_hours else ""
            ]
            writer.writerow(row)
        
        return output.getvalue()
    
    @staticmethod
    def get_low_confidence_events(sof_doc: SoFDocument, threshold: float = 0.7) -> List[SoFEvent]:
        """Get events with confidence below threshold for user editing"""
        return [event for event in sof_doc.events if event.confidence < threshold]
    
    @staticmethod
    def validate_sof_document(text: str) -> Tuple[bool, float, List[str]]:
        """Validate if document is a Statement of Facts"""
        text_lower = text.lower()
        
        sof_indicators = [
            'statement of facts',
            'sof',
            'nor tendered',
            'notice of readiness',
            'berth',
            'loading',
            'discharging',
            'laytime',
            'demurrage',
            'vessel',
            'port'
        ]
        
        found_indicators = []
        confidence_score = 0.0
        
        for indicator in sof_indicators:
            if indicator in text_lower:
                found_indicators.append(indicator)
                confidence_score += 0.1
        
        # Additional scoring based on structure
        if re.search(r'\d{2}:\d{2}.*\d{2}[\/\-]\d{2}[\/\-]\d{2,4}', text):
            confidence_score += 0.2  # Time/date patterns
        
        if re.search(r'(?:commenced?|complet(?:ed)?|start(?:ed)?|finish(?:ed)?)', text, re.IGNORECASE):
            confidence_score += 0.1  # Action words
        
        is_sof = confidence_score >= 0.3
        
        return is_sof, min(confidence_score, 1.0), found_indicators
